import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import (
    Mailing,
    MailingStatus,
    MessageDelivery,
    DeliveryStatus,
    DeliveryChannel,
    User,
    UserRole,
)

logger = logging.getLogger(__name__)


class MailingService:
    @staticmethod
    def get_audience_query(db: Session, recipient_filter: Optional[Dict[str, Any]] = None):
        """Builds a query for subscribers based on filter criteria."""
        query = db.query(User)

        filter_data = recipient_filter or {}
        
        # Filter by active status (default: only active subscribers)
        only_active = filter_data.get("is_active", True)
        if only_active is not None:
            query = query.filter(User.is_active == only_active)

        # By default, target SUBSCRIBER role (unless specified otherwise)
        roles = filter_data.get("roles")
        if roles:
            query = query.filter(User.role.in_(roles))
        else:
            query = query.filter(User.role == UserRole.SUBSCRIBER.value)

        # Filter by tags if provided
        tags = filter_data.get("tags")
        if tags and isinstance(tags, list) and len(tags) > 0:
            # We filter subscribers whose tags_attributes contains any of the required tags
            # Since tags_attributes is JSON, we can do in-memory filtering or SQL expression
            # For cross-DB compatibility (SQLite & Postgres), filter matched users
            all_users = query.all()
            matched_ids = []
            for u in all_users:
                user_tags = u.tags_attributes if isinstance(u.tags_attributes, list) else []
                if any(t in user_tags for t in tags):
                    matched_ids.append(u.id)
            return db.query(User).filter(User.id.in_(matched_ids))

        return query

    @staticmethod
    def count_audience(db: Session, recipient_filter: Optional[Dict[str, Any]] = None) -> int:
        return MailingService.get_audience_query(db, recipient_filter).count()

    @staticmethod
    def prepare_dispatch(db: Session, mailing: Mailing) -> List[str]:
        """
        Creates MessageDelivery records for all recipients idempotently.
        Returns list of delivery IDs created or queued.
        """
        audience_query = MailingService.get_audience_query(db, mailing.recipient_filter)
        recipients = audience_query.all()

        # Existing delivery recipient IDs for idempotency
        existing_deliveries = (
            db.query(MessageDelivery.recipient_id)
            .filter(MessageDelivery.mailing_id == mailing.id)
            .all()
        )
        existing_recipient_ids = {r[0] for r in existing_deliveries}

        delivery_ids = []
        new_deliveries = []

        for recipient in recipients:
            if recipient.id in existing_recipient_ids:
                continue

            delivery = MessageDelivery(
                mailing_id=mailing.id,
                recipient_id=recipient.id,
                channel=DeliveryChannel.EMAIL.value,
                status=DeliveryStatus.PENDING.value,
                retry_count=0,
            )
            new_deliveries.append(delivery)

        if new_deliveries:
            db.add_all(new_deliveries)
            db.flush()
            delivery_ids = [d.id for d in new_deliveries]

        # Update mailing stats
        total_deliveries = (
            db.query(func.count(MessageDelivery.id))
            .filter(MessageDelivery.mailing_id == mailing.id)
            .scalar() or 0
        )
        mailing.total_count = total_deliveries
        mailing.status = MailingStatus.PROCESSING.value
        if not mailing.started_at:
            mailing.started_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(mailing)

        # Return all pending delivery IDs for this mailing
        all_pending = (
            db.query(MessageDelivery.id)
            .filter(
                MessageDelivery.mailing_id == mailing.id,
                MessageDelivery.status == DeliveryStatus.PENDING.value,
            )
            .all()
        )
        return [p[0] for p in all_pending]

    @staticmethod
    def calculate_stats(db: Session, mailing: Mailing) -> Dict[str, Any]:
        """Calculates real-time delivery statistics for a mailing."""
        counts = (
            db.query(MessageDelivery.status, func.count(MessageDelivery.id))
            .filter(MessageDelivery.mailing_id == mailing.id)
            .group_by(MessageDelivery.status)
            .all()
        )
        counts_dict = {status: count for status, count in counts}

        total = mailing.total_count or sum(counts_dict.values())
        success = counts_dict.get(DeliveryStatus.SENT.value, 0) + counts_dict.get(DeliveryStatus.DELIVERED.value, 0)
        failed = counts_dict.get(DeliveryStatus.FAILED.value, 0) + counts_dict.get(DeliveryStatus.BOUNCED.value, 0)
        pending = counts_dict.get(DeliveryStatus.PENDING.value, 0)

        delivery_rate = round((success / total * 100), 2) if total > 0 else 0.0

        duration = None
        if mailing.started_at:
            end_time = mailing.finished_at or datetime.now(timezone.utc)
            duration = round((end_time - mailing.started_at).total_seconds(), 2)

        return {
            "mailing_id": mailing.id,
            "title": mailing.title,
            "status": mailing.status,
            "total_count": total,
            "success_count": success,
            "failed_count": failed,
            "pending_count": pending,
            "delivery_rate_percent": delivery_rate,
            "started_at": mailing.started_at,
            "finished_at": mailing.finished_at,
            "duration_seconds": duration,
            "chart_data": {
                "sent": success,
                "failed": failed,
                "pending": pending,
            },
        }
