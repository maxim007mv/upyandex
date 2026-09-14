import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class DeliveryChannel(str, Enum):
    EMAIL = "EMAIL"
    TELEGRAM = "TELEGRAM"
    SMS = "SMS"


class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"


class MessageDelivery(Base):
    __tablename__ = "message_deliveries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mailing_id = Column(String(36), ForeignKey("mailings.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(20), default=DeliveryChannel.EMAIL.value, nullable=False)
    status = Column(String(20), default=DeliveryStatus.PENDING.value, nullable=False, index=True)
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mailing = relationship("Mailing", back_populates="deliveries")
    recipient = relationship("User", back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("mailing_id", "recipient_id", name="uq_mailing_recipient"),
    )

    def __repr__(self) -> str:
        return f"<MessageDelivery {self.id} {self.status}>"
