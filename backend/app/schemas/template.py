from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TemplateBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    body_content: str = Field(..., min_length=1)
    required_variables: List[str] = Field(default_factory=list)


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    body_content: Optional[str] = Field(None, min_length=1)
    required_variables: Optional[List[str]] = None


class TemplateResponse(TemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplatePreviewRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)


class TemplatePreviewResponse(BaseModel):
    rendered_subject: str
    rendered_body: str
    detected_variables: List[str]
