import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "test_mock"

from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.db.session import Base, get_db
from app.db.models import User, UserRole, MessageTemplate, Mailing, MessageDelivery
from app.services.email_service import email_sender
from app.main import app

# In-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_email_mock():
    email_sender.mock_mode = True
    yield
    email_sender.mock_mode = False


@pytest.fixture(scope="function")
def db() -> Generator:
    from unittest.mock import patch
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    with patch("app.workers.tasks.SessionLocal", side_effect=TestingSessionLocal):
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> Generator:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db) -> User:
    user = User(
        email="admin.test@example.com",
        full_name="Admin Test",
        role=UserRole.ADMIN.value,
        hashed_password=get_password_hash("password123"),
        is_active=True,
        tags_attributes=["admin"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_headers(admin_user) -> dict:
    token = create_access_token(subject=admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_template(db) -> MessageTemplate:
    tpl = MessageTemplate(
        title="Тестовый шаблон",
        subject="Здравствуйте, {{ user.full_name }}!",
        body_content="<p>Текст письма для {{ user.email }}</p><a href='{{ unsubscribe_url }}'>Отписаться</a>",
        required_variables=["user.full_name", "user.email"],
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


@pytest.fixture(scope="function")
def sample_subscribers(db) -> list:
    subs = [
        User(
            email="sub1@example.com",
            full_name="User One",
            phone="+79001111111",
            role=UserRole.SUBSCRIBER.value,
            is_active=True,
            tags_attributes=["vip", "news"],
        ),
        User(
            email="sub2@example.com",
            full_name="User Two",
            phone="+79002222222",
            role=UserRole.SUBSCRIBER.value,
            is_active=True,
            tags_attributes=["news"],
        ),
        User(
            email="sub3@example.com",
            full_name="User Three",
            phone="+79003333333",
            role=UserRole.SUBSCRIBER.value,
            is_active=False,
            tags_attributes=["inactive"],
        ),
    ]
    db.add_all(subs)
    db.commit()
    return subs
