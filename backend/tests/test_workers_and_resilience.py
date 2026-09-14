import pytest
from unittest.mock import patch
from app.db.models import (
    Mailing,
    MailingStatus,
    MessageDelivery,
    DeliveryStatus,
)
from app.services.email_service import PermanentEmailError, TransientEmailError
from app.services.mailing_service import MailingService
from app.workers.tasks import (
    dispatch_mailing_task,
    send_message_task,
    check_and_finalize_mailing,
)


def test_prepare_dispatch_and_idempotency(db, sample_template, sample_subscribers):
    # Create mailing
    mailing = Mailing(
        title="Тест диспетчера",
        template_id=sample_template.id,
        status=MailingStatus.PROCESSING.value,
        recipient_filter={"is_active": True},
    )
    db.add(mailing)
    db.commit()
    db.refresh(mailing)

    # First dispatch preparation
    delivery_ids_1 = MailingService.prepare_dispatch(db, mailing)
    assert len(delivery_ids_1) == 2  # sub1 and sub2 are active

    # Second dispatch preparation for same mailing (Idempotency guarantee!)
    delivery_ids_2 = MailingService.prepare_dispatch(db, mailing)
    assert len(delivery_ids_2) == 2  # returns existing pending, but didn't create duplicates!

    total_deliveries = (
        db.query(MessageDelivery)
        .filter(MessageDelivery.mailing_id == mailing.id)
        .count()
    )
    assert total_deliveries == 2  # Exactly 2 records in DB


def test_send_message_task_success(db, sample_template, sample_subscribers):
    mailing = Mailing(
        title="Тест отправщика",
        template_id=sample_template.id,
        status=MailingStatus.PROCESSING.value,
        recipient_filter={},
    )
    db.add(mailing)
    db.commit()

    delivery_ids = MailingService.prepare_dispatch(db, mailing)
    d_id = delivery_ids[0]

    # Run sender task directly
    res = send_message_task(d_id)
    assert res["status"] == "sent"

    # Verify delivery record in DB
    delivery = db.query(MessageDelivery).filter(MessageDelivery.id == d_id).first()
    assert delivery.status == DeliveryStatus.SENT.value
    assert delivery.sent_at is not None

    # Idempotency check: run sender task a second time
    res_repeat = send_message_task(d_id)
    assert res_repeat["status"] == "already_sent"


def test_send_message_task_cancelled_resilience(db, sample_template, sample_subscribers):
    mailing = Mailing(
        title="Отмененная кампания",
        template_id=sample_template.id,
        status=MailingStatus.CANCELLED.value,
        recipient_filter={},
    )
    db.add(mailing)
    db.commit()

    delivery = MessageDelivery(
        mailing_id=mailing.id,
        recipient_id=sample_subscribers[0].id,
        status=DeliveryStatus.PENDING.value,
    )
    db.add(delivery)
    db.commit()

    # Worker attempts to send, but should recognize CANCELLED status
    res = send_message_task(delivery.id)
    assert res["status"] == "cancelled"

    db.refresh(delivery)
    assert delivery.status == DeliveryStatus.PENDING.value  # not sent!


def test_send_message_task_permanent_error_handling(db, sample_template, sample_subscribers):
    mailing = Mailing(
        title="Тест сбоя",
        template_id=sample_template.id,
        status=MailingStatus.PROCESSING.value,
        recipient_filter={},
    )
    db.add(mailing)
    db.commit()

    delivery = MessageDelivery(
        mailing_id=mailing.id,
        recipient_id=sample_subscribers[0].id,
        status=DeliveryStatus.PENDING.value,
    )
    db.add(delivery)
    db.commit()

    with patch("app.workers.tasks.email_sender.send_email", side_effect=PermanentEmailError("Mailbox not found (550)")):
        res = send_message_task(delivery.id)
        assert res["status"] == "failed"

    db.refresh(delivery)
    assert delivery.status == DeliveryStatus.FAILED.value
    assert "Mailbox not found" in delivery.error_message

    db.refresh(mailing)
    assert mailing.failed_count == 1
