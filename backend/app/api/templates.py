from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import MessageTemplate, Mailing, MailingStatus, User
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from app.services.template_service import TemplateService
from app.api.deps import get_current_admin

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=List[TemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all message templates."""
    return db.query(MessageTemplate).order_by(MessageTemplate.created_at.desc()).all()


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    tpl_in: TemplateCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new message template with Jinja2 syntax validation."""
    # Validate subject syntax
    valid_sub, err_sub = TemplateService.validate_template(tpl_in.subject)
    if not valid_sub:
        raise HTTPException(status_code=400, detail=f"Subject syntax error: {err_sub}")

    # Validate body syntax
    valid_body, err_body = TemplateService.validate_template(tpl_in.body_content)
    if not valid_body:
        raise HTTPException(status_code=400, detail=f"Body syntax error: {err_body}")

    # Extract detected variables if not provided
    vars_subject = TemplateService.extract_variables(tpl_in.subject)
    vars_body = TemplateService.extract_variables(tpl_in.body_content)
    auto_vars = sorted(list(set(vars_subject + vars_body)))

    req_vars = tpl_in.required_variables if tpl_in.required_variables else auto_vars

    template = MessageTemplate(
        title=tpl_in.title,
        subject=tpl_in.subject,
        body_content=tpl_in.body_content,
        required_variables=req_vars,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{id}", response_model=TemplateResponse)
def get_template(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    template = db.query(MessageTemplate).filter(MessageTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{id}", response_model=TemplateResponse)
def update_template(
    id: str,
    tpl_in: TemplateUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    template = db.query(MessageTemplate).filter(MessageTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if tpl_in.subject is not None:
        valid_sub, err_sub = TemplateService.validate_template(tpl_in.subject)
        if not valid_sub:
            raise HTTPException(status_code=400, detail=f"Subject syntax error: {err_sub}")
        template.subject = tpl_in.subject

    if tpl_in.body_content is not None:
        valid_body, err_body = TemplateService.validate_template(tpl_in.body_content)
        if not valid_body:
            raise HTTPException(status_code=400, detail=f"Body syntax error: {err_body}")
        template.body_content = tpl_in.body_content

    if tpl_in.title is not None:
        template.title = tpl_in.title

    if tpl_in.required_variables is not None:
        template.required_variables = tpl_in.required_variables
    else:
        # Re-extract variables
        vars_subject = TemplateService.extract_variables(template.subject)
        vars_body = TemplateService.extract_variables(template.body_content)
        template.required_variables = sorted(list(set(vars_subject + vars_body)))

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    template = db.query(MessageTemplate).filter(MessageTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check if template is used by active mailings
    active_mailings = (
        db.query(Mailing)
        .filter(
            Mailing.template_id == id,
            Mailing.status.in_([MailingStatus.SCHEDULED.value, MailingStatus.PROCESSING.value]),
        )
        .count()
    )
    if active_mailings > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete template that is currently referenced by active or scheduled mailings",
        )

    db.delete(template)
    db.commit()
    return None


@router.post("/{id}/preview", response_model=TemplatePreviewResponse)
def preview_template(
    id: str,
    preview_data: TemplatePreviewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Render a template preview using provided or sample test context."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Fallback default test variables
    default_context = {
        "user": {
            "id": "sample-uuid",
            "email": "preview.user@example.com",
            "full_name": "Иван Тестовый",
            "phone": "+79991234567",
            "tags": ["vip", "preview"],
        },
        "unsubscribe_url": "http://localhost:5173/unsubscribe?token=sample_preview_token",
        "current_year": 2026,
    }

    # Merge user provided variables
    context = {**default_context, **preview_data.variables}

    rendered_subject = TemplateService.render(template.subject, context)
    rendered_body = TemplateService.render(template.body_content, context)

    vars_subject = TemplateService.extract_variables(template.subject)
    vars_body = TemplateService.extract_variables(template.body_content)
    detected = sorted(list(set(vars_subject + vars_body)))

    return {
        "rendered_subject": rendered_subject,
        "rendered_body": rendered_body,
        "detected_variables": detected,
    }
