import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CLIENT = "CLIENT"
    SUBSCRIBER = "SUBSCRIBER"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(20), default=UserRole.SUBSCRIBER.value, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    tags_attributes = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    created_mailings = relationship("Mailing", back_populates="author", cascade="all, delete-orphan", foreign_keys="Mailing.author_id")
    deliveries = relationship("MessageDelivery", back_populates="recipient", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
