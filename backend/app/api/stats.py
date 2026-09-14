from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.db.models import (
    User,
    UserRole,
    Mailing,
    MailingStatus,
    MessageDelivery,
    DeliveryStatus,
    MessageTemplate,
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def get_global_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Global system overview metrics for the dashboard."""
    total_subscribers = db.query(User).filter(User.role == UserRole.SUBSCRIBER.value).count()
    active_subscribers = db.query(User).filter(User.role == UserRole.SUBSCRIBER.value, User.is_active == True).count()
    inactive_subscribers = total_subscribers - active_subscribers

    total_mailings = db.query(Mailing).count()
    active_mailings = db.query(Mailing).filter(Mailing.status == MailingStatus.PROCESSING.value).count()
    scheduled_mailings = db.query(Mailing).filter(Mailing.status == MailingStatus.SCHEDULED.value).count()
    completed_mailings = db.query(Mailing).filter(Mailing.status == MailingStatus.COMPLETED.value).count()

    total_templates = db.query(MessageTemplate).count()

    # Message delivery counts
    total_messages = db.query(MessageDelivery).count()
    sent_messages = db.query(MessageDelivery).filter(
        MessageDelivery.status.in_([DeliveryStatus.SENT.value, DeliveryStatus.DELIVERED.value])
    ).count()
    failed_messages = db.query(MessageDelivery).filter(
        MessageDelivery.status.in_([DeliveryStatus.FAILED.value, DeliveryStatus.BOUNCED.value])
    ).count()
    pending_messages = db.query(MessageDelivery).filter(
        MessageDelivery.status == DeliveryStatus.PENDING.value
    ).count()

    delivery_rate = round((sent_messages / total_messages * 100), 2) if total_messages > 0 else 100.0

    recent_mailings = (
        db.query(Mailing)
        .order_by(Mailing.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "subscribers": {
            "total": total_subscribers,
            "active": active_subscribers,
            "inactive": inactive_subscribers,
        },
        "mailings": {
            "total": total_mailings,
            "active": active_mailings,
            "scheduled": scheduled_mailings,
            "completed": completed_mailings,
        },
        "messages": {
            "total": total_messages,
            "sent": sent_messages,
            "failed": failed_messages,
            "pending": pending_messages,
            "delivery_rate_percent": delivery_rate,
        },
        "templates_count": total_templates,
        "recent_mailings": [
            {
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "total_count": m.total_count,
                "success_count": m.success_count,
                "failed_count": m.failed_count,
                "created_at": m.created_at,
            }
            for m in recent_mailings
        ],
    }
