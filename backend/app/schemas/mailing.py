from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.template import TemplateResponse
from app.schemas.auth import UserResponse


class MailingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: str
    recipient_filter: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None


class MailingCreate(MailingBase):
    pass


class MailingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: Optional[str] = None
    recipient_filter: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class MailingResponse(MailingBase):
    id: str
    author_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime
    template: Optional[TemplateResponse] = None
    author: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class MailingListResponse(BaseModel):
    items: List[MailingResponse]
    total: int
    page: int
    size: int


class MailingStatsResponse(BaseModel):
    mailing_id: str
    title: str
    status: str
    total_count: int
    success_count: int
    failed_count: int
    pending_count: int
    delivery_rate_percent: float
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    chart_data: Optional[Dict[str, int]] = None
