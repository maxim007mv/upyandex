import logging
from datetime import datetime, timezone
from celery import shared_task
from app.db.session import SessionLocal
from app.db.models import (
    Mailing,
    MailingStatus,
    MessageDelivery,
    DeliveryStatus,
    User,
    MessageTemplate,
)
from app.services.email_service import (
    email_sender,
    TransientEmailError,
    PermanentEmailError,
    EmailTransportError,
)
from app.services.template_service import TemplateService
from app.services.mailing_service import MailingService
from app.core.security import generate_unsubscribe_token
from app.core.config import settings

logger = logging.getLogger(__name__)


def check_and_finalize_mailing(db, mailing_id: str):
    """Helper to check if all deliveries are done and update mailing status accordingly."""
    mailing = db.query(Mailing).filter(Mailing.id == mailing_id).first()
    if not mailing:
        return

    # Check remaining pending deliveries
    pending_count = (
        db.query(MessageDelivery)
        .filter(
            MessageDelivery.mailing_id == mailing_id,
            MessageDelivery.status == DeliveryStatus.PENDING.value,
        )
        .count()
    )

    if pending_count == 0:
        mailing.finished_at = datetime.now(timezone.utc)
        if mailing.status == MailingStatus.CANCELLED.value:
            logger.info(f"Mailing {mailing_id} was cancelled, finalized as CANCELLED")
        elif mailing.success_count == 0 and mailing.failed_count > 0:
            mailing.status = MailingStatus.FAILED.value
            logger.warning(f"Mailing {mailing_id} completed with all failed messages -> FAILED")
        else:
            mailing.status = MailingStatus.COMPLETED.value
            logger.info(f"Mailing {mailing_id} successfully completed all messages -> COMPLETED")
        db.commit()


@shared_task(bind=True, name="app.workers.tasks.dispatch_mailing_task")
def dispatch_mailing_task(self, mailing_id: str):
    """
    Dispatcher task: loads the mailing, creates MessageDelivery records,
    and fans out atomic send_message_task tasks for each recipient.
    """
    logger.info(f"Starting dispatch for mailing {mailing_id}")
    db = SessionLocal()
    try:
        mailing = db.query(Mailing).filter(Mailing.id == mailing_id).first()
        if not mailing:
            logger.error(f"Mailing {mailing_id} not found")
            return {"status": "error", "message": "Mailing not found"}

        if mailing.status == MailingStatus.CANCELLED.value:
            logger.warning(f"Mailing {mailing_id} is cancelled, aborting dispatch")
            return {"status": "aborted", "reason": "cancelled"}

        # Prepare MessageDelivery records idempotently
        delivery_ids = MailingService.prepare_dispatch(db, mailing)
        logger.info(f"Prepared {len(delivery_ids)} deliveries for mailing {mailing_id}")

        if not delivery_ids:
            # No recipients matched the filter
            mailing.finished_at = datetime.now(timezone.utc)
            mailing.status = MailingStatus.COMPLETED.value
            db.commit()
            return {"status": "completed", "count": 0}

        # Fan out send_message_task for each delivery
        for delivery_id in delivery_ids:
            send_message_task.delay(delivery_id)

        return {"status": "dispatched", "count": len(delivery_ids)}
    except Exception as e:
        logger.error(f"Error in dispatch_mailing_task for {mailing_id}: {e}", exc_info=True)
        if 'mailing' in locals() and mailing:
            mailing.status = MailingStatus.FAILED.value
            db.commit()
        raise
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name="app.workers.tasks.send_message_task")
def send_message_task(self, delivery_id: str):
    """
    Sender task: sends a single email message, updates delivery record,
    and handles retries with exponential backoff.
    """
    db = SessionLocal()
    try:
        delivery = db.query(MessageDelivery).filter(MessageDelivery.id == delivery_id).first()
        if not delivery:
            logger.error(f"Delivery {delivery_id} not found")
            return {"status": "error", "message": "Delivery not found"}

        mailing = db.query(Mailing).filter(Mailing.id == delivery.mailing_id).first()
        if not mailing:
            logger.error(f"Mailing {delivery.mailing_id} not found for delivery {delivery_id}")
            return {"status": "error", "message": "Mailing not found"}

        # Check if mailing was cancelled
        if mailing.status == MailingStatus.CANCELLED.value:
            logger.info(f"Skipping delivery {delivery_id} because mailing {mailing.id} is CANCELLED")
            return {"status": "cancelled"}

        # Idempotency check: don't re-send already sent messages
        if delivery.status in (DeliveryStatus.SENT.value, DeliveryStatus.DELIVERED.value):
            logger.info(f"Delivery {delivery_id} already sent, skipping (Idempotency guarantee)")
            return {"status": "already_sent"}

        recipient = db.query(User).filter(User.id == delivery.recipient_id).first()
        if not recipient or not recipient.is_active:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.error_message = "Recipient inactive or removed"
            mailing.failed_count += 1
            db.commit()
            check_and_finalize_mailing(db, mailing.id)
            return {"status": "failed", "reason": "recipient_inactive"}

        template = db.query(MessageTemplate).filter(MessageTemplate.id == mailing.template_id).first()
        if not template:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.error_message = "Template not found"
            mailing.failed_count += 1
            db.commit()
            check_and_finalize_mailing(db, mailing.id)
            return {"status": "failed", "reason": "template_missing"}

        # Build context for template rendering
        unsubscribe_token = generate_unsubscribe_token(recipient.id, recipient.email)
        unsubscribe_url = f"{settings.UNSUBSCRIBE_BASE_URL}?token={unsubscribe_token}"

        user_context = {
            "id": recipient.id,
            "email": recipient.email,
            "full_name": recipient.full_name or recipient.email,
            "phone": recipient.phone or "",
            "tags": recipient.tags_attributes or [],
        }

        render_context = {
            "user": user_context,
            "unsubscribe_url": unsubscribe_url,
            "current_year": datetime.now(timezone.utc).year,
        }

        # Render subject and body
        rendered_subject = TemplateService.render(template.subject, render_context)
        rendered_body = TemplateService.render(template.body_content, render_context)

        # Attempt to send
        try:
            msg_id = email_sender.send_email(
                to_email=recipient.email,
                subject=rendered_subject,
                html_content=rendered_body,
                unsubscribe_url=unsubscribe_url,
            )

            delivery.status = DeliveryStatus.SENT.value
            delivery.sent_at = datetime.now(timezone.utc)
            delivery.error_message = None
            mailing.success_count += 1
            db.commit()
            logger.info(f"Delivery {delivery_id} completed successfully (Msg-ID: {msg_id})")

            check_and_finalize_mailing(db, mailing.id)
            return {"status": "sent", "delivery_id": delivery_id}

        except TransientEmailError as e:
            # Network issue, rate limit, timeout -> retry with backoff
            logger.warning(f"Transient error sending delivery {delivery_id} (Attempt {self.request.retries + 1}/3): {e}")
            delivery.retry_count = self.request.retries + 1
            delivery.error_message = f"Transient error (Attempt {delivery.retry_count}): {str(e)}"
            db.commit()

            countdown = (2 ** self.request.retries) * 10  # 10s, 20s, 40s
            raise self.retry(exc=e, countdown=countdown)

        except (PermanentEmailError, Exception) as e:
            # Permanent error or unhandled failure
            logger.error(f"Permanent error sending delivery {delivery_id}: {e}")
            delivery.status = DeliveryStatus.FAILED.value
            delivery.error_message = str(e)
            mailing.failed_count += 1
            db.commit()

            check_and_finalize_mailing(db, mailing.id)
            return {"status": "failed", "error": str(e)}

    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for delivery {delivery_id}")
        delivery = db.query(MessageDelivery).filter(MessageDelivery.id == delivery_id).first()
        if delivery:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.error_message = "Max retries exceeded (transient connection failures)"
            mailing = db.query(Mailing).filter(Mailing.id == delivery.mailing_id).first()
            if mailing:
                mailing.failed_count += 1
            db.commit()
            if mailing:
                check_and_finalize_mailing(db, mailing.id)
        return {"status": "failed", "reason": "max_retries_exceeded"}
    finally:
        db.close()


@shared_task(name="app.workers.tasks.check_scheduled_mailings_task")
def check_scheduled_mailings_task():
    """
    Celery Beat task: checks for SCHEDULED mailings that should be started now.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        scheduled_mailings = (
            db.query(Mailing)
            .filter(
                Mailing.status == MailingStatus.SCHEDULED.value,
                Mailing.scheduled_at <= now,
            )
            .all()
        )

        logger.info(f"Found {len(scheduled_mailings)} scheduled mailings ready for execution")
        for m in scheduled_mailings:
            m.status = MailingStatus.PROCESSING.value
            m.started_at = now
            db.commit()
            dispatch_mailing_task.delay(m.id)

        return {"triggered_count": len(scheduled_mailings)}
    finally:
        db.close()
