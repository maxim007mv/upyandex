import pytest
from fastapi import status


def test_login_success(client, admin_user):
    response = client.post(
        "/api/v1/auth/login/json",
        json={"email": admin_user.email, "password": "password123"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == admin_user.email


def test_login_invalid_password(client, admin_user):
    response = client.post(
        "/api/v1/auth/login/json",
        json={"email": admin_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_current_user_me(client, admin_headers, admin_user):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == admin_user.id
    assert data["email"] == admin_user.email


def test_get_current_user_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
