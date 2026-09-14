import pytest
from fastapi import status


def test_create_template_valid(client, admin_headers):
    response = client.post(
        "/api/v1/templates",
        headers=admin_headers,
        json={
            "title": "Welcome Email",
            "subject": "Добро пожаловать, {{ user.full_name }}!",
            "body_content": "<h1>Привет!</h1><p>Ваш email: {{ user.email }}</p>",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Welcome Email"
    assert "user.full_name" in data["required_variables"]
    assert "user.email" in data["required_variables"]


def test_create_template_invalid_syntax(client, admin_headers):
    # Invalid Jinja2 syntax
    response = client.post(
        "/api/v1/templates",
        headers=admin_headers,
        json={
            "title": "Broken Template",
            "subject": "Hello {{ user.full_name",
            "body_content": "<p>Content</p>",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Subject syntax error" in response.json()["detail"]


def test_preview_template(client, admin_headers, sample_template):
    response = client.post(
        f"/api/v1/templates/{sample_template.id}/preview",
        headers=admin_headers,
        json={
            "variables": {
                "user": {"full_name": "Тестовый Пользователь", "email": "test@test.com"},
                "unsubscribe_url": "http://example.com/unsub",
            }
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "Тестовый Пользователь" in data["rendered_subject"]
    assert "test@test.com" in data["rendered_body"]
    assert "http://example.com/unsub" in data["rendered_body"]
