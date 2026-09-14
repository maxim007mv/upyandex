import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.db.session import get_db
from app.db.models import User, UserRole
from app.schemas.subscriber import (
    SubscriberCreate,
    SubscriberUpdate,
    SubscriberResponse,
    SubscriberListResponse,
    BatchImportResult,
    BatchImportError,
    UnsubscribeRequest,
)
from app.api.deps import get_current_admin
from app.core.security import verify_unsubscribe_token

router = APIRouter(prefix="/subscribers", tags=["subscribers"])


@router.get("", response_model=SubscriberListResponse)
def get_subscribers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List subscribers with filtering and pagination."""
    query = db.query(User).filter(User.role == UserRole.SUBSCRIBER.value)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
                User.phone.ilike(search_pattern),
            )
        )

    # Filter by tag in tags_attributes JSON
    if tag:
        all_candidates = query.all()
        matched_ids = [
            u.id for u in all_candidates
            if isinstance(u.tags_attributes, list) and tag in u.tags_attributes
        ]
        query = db.query(User).filter(User.id.in_(matched_ids))

    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/tags", response_model=List[str])
def get_subscriber_tags(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Returns all unique tags used across subscribers."""
    subscribers = db.query(User.tags_attributes).filter(User.role == UserRole.SUBSCRIBER.value).all()
    unique_tags = set()
    for row in subscribers:
        tags = row[0]
        if isinstance(tags, list):
            for t in tags:
                if t:
                    unique_tags.add(t.strip())
    return sorted(list(unique_tags))


@router.post("", response_model=SubscriberResponse, status_code=status.HTTP_201_CREATED)
def create_subscriber(
    subscriber_in: SubscriberCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Add a new subscriber."""
    existing = db.query(User).filter(User.email == subscriber_in.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subscriber with email '{subscriber_in.email}' already exists",
        )

    subscriber = User(
        email=subscriber_in.email.lower(),
        full_name=subscriber_in.full_name,
        phone=subscriber_in.phone,
        role=UserRole.SUBSCRIBER.value,
        is_active=subscriber_in.is_active,
        tags_attributes=subscriber_in.tags_attributes or [],
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


@router.post("/import-csv", response_model=BatchImportResult)
async def import_subscribers_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Import subscribers from a CSV file.
    Expected header columns: email, full_name (optional), phone (optional), tags (comma/semicolon separated).
    """
    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            decoded = content.decode("cp1251")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode CSV file. Use UTF-8 or CP1251 encoding.")

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or missing headers")

    # Normalize fieldnames
    headers_map = {h.strip().lower(): h for h in reader.fieldnames}
    email_col = headers_map.get("email") or headers_map.get("почта") or headers_map.get("e-mail")
    if not email_col:
        raise HTTPException(status_code=400, detail="Missing required 'email' column in CSV header")

    name_col = headers_map.get("full_name") or headers_map.get("name") or headers_map.get("имя") or headers_map.get("фио")
    phone_col = headers_map.get("phone") or headers_map.get("телефон") or headers_map.get("тел")
    tags_col = headers_map.get("tags") or headers_map.get("теги")

    added = 0
    updated = 0
    errors: List[BatchImportError] = []

    for line_num, row in enumerate(reader, start=2):
        raw_email = (row.get(email_col) or "").strip().lower()
        if not raw_email or "@" not in raw_email:
            errors.append(BatchImportError(line=line_num, email=raw_email, error="Invalid email address"))
            continue

        raw_name = (row.get(name_col) or "").strip() if name_col else None
        raw_phone = (row.get(phone_col) or "").strip() if phone_col else None
        raw_tags_str = (row.get(tags_col) or "").strip() if tags_col else ""

        # Parse tags
        tags = []
        if raw_tags_str:
            delimiter = ";" if ";" in raw_tags_str else ","
            tags = [t.strip() for t in raw_tags_str.split(delimiter) if t.strip()]

        existing = db.query(User).filter(User.email == raw_email).first()
        if existing:
            # Update attributes
            if raw_name:
                existing.full_name = raw_name
            if raw_phone:
                existing.phone = raw_phone
            if tags:
                cur_tags = set(existing.tags_attributes or [])
                cur_tags.update(tags)
                existing.tags_attributes = list(cur_tags)
            existing.is_active = True
            updated += 1
        else:
            new_sub = User(
                email=raw_email,
                full_name=raw_name,
                phone=raw_phone,
                role=UserRole.SUBSCRIBER.value,
                is_active=True,
                tags_attributes=tags,
            )
            db.add(new_sub)
            added += 1

    db.commit()
    return {
        "total_processed": added + updated + len(errors),
        "added": added,
        "updated": updated,
        "errors": errors,
    }


@router.get("/{id}", response_model=SubscriberResponse)
def get_subscriber(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    subscriber = db.query(User).filter(User.id == id, User.role == UserRole.SUBSCRIBER.value).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return subscriber


@router.put("/{id}", response_model=SubscriberResponse)
def update_subscriber(
    id: str,
    sub_in: SubscriberUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    subscriber = db.query(User).filter(User.id == id, User.role == UserRole.SUBSCRIBER.value).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    if sub_in.email is not None and sub_in.email.lower() != subscriber.email:
        conflict = db.query(User).filter(User.email == sub_in.email.lower(), User.id != id).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Email already taken by another user")
        subscriber.email = sub_in.email.lower()

    if sub_in.full_name is not None:
        subscriber.full_name = sub_in.full_name
    if sub_in.phone is not None:
        subscriber.phone = sub_in.phone
    if sub_in.is_active is not None:
        subscriber.is_active = sub_in.is_active
    if sub_in.tags_attributes is not None:
        subscriber.tags_attributes = sub_in.tags_attributes

    db.commit()
    db.refresh(subscriber)
    return subscriber


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscriber(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    subscriber = db.query(User).filter(User.id == id, User.role == UserRole.SUBSCRIBER.value).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    db.delete(subscriber)
    db.commit()
    return None


@router.patch("/{id}/unsubscribe", response_model=SubscriberResponse)
def admin_unsubscribe_subscriber(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Admin endpoint to deactivate/unsubscribe a user."""
    subscriber = db.query(User).filter(User.id == id).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    subscriber.is_active = False
    db.commit()
    db.refresh(subscriber)
    return subscriber


@router.post("/unsubscribe-by-token")
def public_unsubscribe_by_token(
    payload: UnsubscribeRequest,
    db: Session = Depends(get_db),
):
    """Public token-based 1-click unsubscribe endpoint."""
    token_data = verify_unsubscribe_token(payload.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired unsubscribe link")

    subscriber_id = token_data.get("sub")
    subscriber = db.query(User).filter(User.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber account not found")

    subscriber.is_active = False
    db.commit()
    return {"status": "success", "message": f"Successfully unsubscribed {subscriber.email}"}
