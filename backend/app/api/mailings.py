import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.db.models import (
    Mailing,
    MailingStatus,
    MessageTemplate,
    MessageDelivery,
    DeliveryStatus,
    User,
)
from app.schemas.mailing import (
    MailingCreate,
    MailingUpdate,
    MailingResponse,
    MailingListResponse,
    MailingStatsResponse,
)
from app.schemas.delivery import (
    DeliveryListResponse,
    DeliveryLogResponse,
)
from app.services.mailing_service import MailingService
from app.api.deps import get_current_admin
from app.workers.tasks import dispatch_mailing_task, send_message_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mailings", tags=["mailings"])


def trigger_dispatch_safe(mailing_id: str):
    """Triggers Celery dispatch task; if Celery/broker is unreachable, runs locally."""
    try:
        dispatch_mailing_task.delay(mailing_id)
    except Exception as e:
        logger.warning(f"Could not queue Celery task via broker ({e}), executing inline fallback")
        dispatch_mailing_task(mailing_id)


def trigger_send_safe(delivery_id: str):
    """Triggers Celery send task; if Celery/broker is unreachable, runs locally."""
    try:
        send_message_task.delay(delivery_id)
    except Exception as e:
        logger.warning(f"Could not queue Celery send task via broker ({e}), executing inline fallback")
        send_message_task(delivery_id)


@router.get("", response_model=MailingListResponse)
def get_mailings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all mailing campaigns with optional status filtering."""
    query = db.query(Mailing)
    if status_filter:
        query = query.filter(Mailing.status == status_filter.upper())

    total = query.count()
    items = query.order_by(Mailing.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("", response_model=MailingResponse, status_code=status.HTTP_201_CREATED)
def create_mailing(
    mailing_in: MailingCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new mailing campaign."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == mailing_in.template_id).first()
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")

    status_val = MailingStatus.DRAFT.value
    if mailing_in.scheduled_at:
        if mailing_in.scheduled_at <= datetime.now(timezone.utc):
            status_val = MailingStatus.PROCESSING.value
        else:
            status_val = MailingStatus.SCHEDULED.value

    # Estimate audience size
    audience_count = MailingService.count_audience(db, mailing_in.recipient_filter)

    mailing = Mailing(
        title=mailing_in.title,
        description=mailing_in.description,
        template_id=mailing_in.template_id,
        author_id=admin.id,
        status=status_val,
        recipient_filter=mailing_in.recipient_filter or {},
        scheduled_at=mailing_in.scheduled_at,
        total_count=audience_count,
    )
    db.add(mailing)
    db.commit()
    db.refresh(mailing)

    # If scheduled for now, trigger dispatch immediately
    if status_val == MailingStatus.PROCESSING.value:
        mailing.started_at = datetime.now(timezone.utc)
        db.commit()
        trigger_dispatch_safe(mailing.id)

    return mailing


@router.get("/{id}", response_model=MailingResponse)
def get_mailing(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get detailed mailing information."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    return mailing


@router.put("/{id}", response_model=MailingResponse)
def update_mailing(
    id: str,
    mailing_in: MailingUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a draft or scheduled mailing."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")

    if mailing.status not in (MailingStatus.DRAFT.value, MailingStatus.SCHEDULED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit mailing in status '{mailing.status}'",
        )

    if mailing_in.template_id:
        tpl = db.query(MessageTemplate).filter(MessageTemplate.id == mailing_in.template_id).first()
        if not tpl:
            raise HTTPException(status_code=400, detail="Template not found")
        mailing.template_id = mailing_in.template_id

    if mailing_in.title is not None:
        mailing.title = mailing_in.title
    if mailing_in.description is not None:
        mailing.description = mailing_in.description
    if mailing_in.recipient_filter is not None:
        mailing.recipient_filter = mailing_in.recipient_filter
        mailing.total_count = MailingService.count_audience(db, mailing_in.recipient_filter)
    if mailing_in.scheduled_at is not None:
        mailing.scheduled_at = mailing_in.scheduled_at
        mailing.status = MailingStatus.SCHEDULED.value if mailing_in.scheduled_at > datetime.now(timezone.utc) else MailingStatus.DRAFT.value

    db.commit()
    db.refresh(mailing)
    return mailing


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mailing(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a mailing and its delivery logs."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")

    if mailing.status == MailingStatus.PROCESSING.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an ongoing processing mailing. Cancel it first.",
        )

    db.delete(mailing)
    db.commit()
    return None


@router.post("/{id}/start", response_model=MailingResponse)
def start_mailing_now(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Immediately start dispatching a mailing campaign."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")

    if mailing.status not in (MailingStatus.DRAFT.value, MailingStatus.SCHEDULED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start mailing with status '{mailing.status}'. Only DRAFT or SCHEDULED mailings can be started.",
        )

    mailing.status = MailingStatus.PROCESSING.value
    mailing.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mailing)

    trigger_dispatch_safe(mailing.id)
    return mailing


@router.post("/{id}/cancel", response_model=MailingResponse)
def cancel_mailing(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Cancel a scheduled or in-progress mailing campaign."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")

    if mailing.status in (MailingStatus.COMPLETED.value, MailingStatus.CANCELLED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Mailing is already {mailing.status}",
        )

    mailing.status = MailingStatus.CANCELLED.value
    mailing.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mailing)
    return mailing


@router.get("/{id}/stats", response_model=MailingStatsResponse)
def get_mailing_stats(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get delivery metrics and rates for a mailing."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")

    return MailingService.calculate_stats(db, mailing)


@router.get("/{id}/messages", response_model=DeliveryListResponse)
def get_mailing_messages(
    id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get delivery log messages for a mailing with status filtering."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")

    query = db.query(MessageDelivery).filter(MessageDelivery.mailing_id == id)
    if status_filter:
        query = query.filter(MessageDelivery.status == status_filter.upper())

    total = query.count()
    deliveries = query.order_by(MessageDelivery.updated_at.desc()).offset((page - 1) * size).limit(size).all()

    items = []
    for d in deliveries:
        items.append(
            DeliveryLogResponse(
                id=d.id,
                mailing_id=d.mailing_id,
                recipient_id=d.recipient_id,
                recipient_email=d.recipient.email if d.recipient else "unknown",
                recipient_name=d.recipient.full_name if d.recipient else None,
                channel=d.channel,
                status=d.status,
                retry_count=d.retry_count,
                error_message=d.error_message,
                sent_at=d.sent_at,
                updated_at=d.updated_at,
            )
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/{id}/retry-failed")
def retry_failed_messages(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Retry all failed messages for this mailing."""
    mailing = db.query(Mailing).filter(Mailing.id == id).first()
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")

    failed_deliveries = (
        db.query(MessageDelivery)
        .filter(
            MessageDelivery.mailing_id == id,
            MessageDelivery.status == DeliveryStatus.FAILED.value,
        )
        .all()
    )

    if not failed_deliveries:
        return {"retried_count": 0, "message": "No failed messages to retry"}

    count = 0
    for d in failed_deliveries:
        d.status = DeliveryStatus.PENDING.value
        d.error_message = None
        count += 1
        trigger_send_safe(d.id)

    # Adjust failed count and set status back to processing
    mailing.failed_count = max(0, mailing.failed_count - count)
    mailing.status = MailingStatus.PROCESSING.value
    mailing.finished_at = None
    db.commit()

    return {"retried_count": count, "message": f"Queued {count} failed messages for retry"}
