from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class SubscriberBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    tags_attributes: List[str] = Field(default_factory=list)
    is_active: bool = True


class SubscriberCreate(SubscriberBase):
    pass


class SubscriberUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    tags_attributes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SubscriberResponse(SubscriberBase):
    id: str
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriberListResponse(BaseModel):
    items: List[SubscriberResponse]
    total: int
    page: int
    size: int


class BatchImportError(BaseModel):
    line: int
    email: Optional[str] = None
    error: str


class BatchImportResult(BaseModel):
    total_processed: int
    added: int
    updated: int
    errors: List[BatchImportError] = []


class UnsubscribeRequest(BaseModel):
    token: str
    reason: Optional[str] = None
