import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class MailingStatus(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Mailing(Base):
    __tablename__ = "mailings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    template_id = Column(String(36), ForeignKey("message_templates.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), default=MailingStatus.DRAFT.value, nullable=False, index=True)
    recipient_filter = Column(JSON, default=dict, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    total_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    author = relationship("User", back_populates="created_mailings", foreign_keys=[author_id])
    template = relationship("MessageTemplate", back_populates="mailings")
    deliveries = relationship("MessageDelivery", back_populates="mailing", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Mailing {self.title} [{self.status}]>"
