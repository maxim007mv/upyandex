import io
import pytest
from fastapi import status
from app.core.security import generate_unsubscribe_token


def test_create_subscriber(client, admin_headers):
    response = client.post(
        "/api/v1/subscribers",
        headers=admin_headers,
        json={
            "email": "new.sub@example.com",
            "full_name": "New Subscriber",
            "phone": "+79998887766",
            "tags_attributes": ["vip", "early-adopter"],
            "is_active": True,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "new.sub@example.com"
    assert "vip" in data["tags_attributes"]


def test_list_subscribers_with_filters(client, admin_headers, sample_subscribers):
    # Filter by tag
    res_vip = client.get("/api/v1/subscribers?tag=vip", headers=admin_headers)
    assert res_vip.status_code == status.HTTP_200_OK
    assert res_vip.json()["total"] == 1
    assert res_vip.json()["items"][0]["email"] == "sub1@example.com"

    # Filter by active
    res_active = client.get("/api/v1/subscribers?is_active=true", headers=admin_headers)
    assert res_active.status_code == status.HTTP_200_OK
    assert res_active.json()["total"] == 2


def test_import_csv(client, admin_headers):
    csv_content = """email,full_name,phone,tags
imported1@example.com,Иван Иванов,+79990001122,vip;marketing
imported2@example.com,Ольга Петрова,,dev
bad_email_no_at,Ошибка,,
"""
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))
    response = client.post(
        "/api/v1/subscribers/import-csv",
        headers=admin_headers,
        files={"file": ("subscribers.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["added"] == 2
    assert len(data["errors"]) == 1


def test_public_token_unsubscribe(client, db, sample_subscribers):
    target = sample_subscribers[0]
    token = generate_unsubscribe_token(target.id, target.email)

    response = client.post(
        "/api/v1/subscribers/unsubscribe-by-token",
        json={"token": token},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "success"

    # Verify db status
    db.refresh(target)
    assert target.is_active is False
