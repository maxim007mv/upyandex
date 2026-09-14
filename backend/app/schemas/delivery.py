from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DeliveryLogResponse(BaseModel):
    id: str
    mailing_id: str
    recipient_id: str
    recipient_email: str
    recipient_name: Optional[str] = None
    channel: str
    status: str
    retry_count: int
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryListResponse(BaseModel):
    items: List[DeliveryLogResponse]
    total: int
    page: int
    size: int
