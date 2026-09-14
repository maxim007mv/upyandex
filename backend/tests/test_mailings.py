import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status
from app.db.models import Mailing, MailingStatus


def test_create_mailing_draft(client, admin_headers, sample_template, sample_subscribers):
    response = client.post(
        "/api/v1/mailings",
        headers=admin_headers,
        json={
            "title": "Первая кампания",
            "description": "Тестовое описание",
            "template_id": sample_template.id,
            "recipient_filter": {"tags": ["vip"]},
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Первая кампания"
    assert data["status"] == MailingStatus.DRAFT.value
    assert data["total_count"] == 1  # only sub1 has 'vip'


def test_start_and_cancel_mailing(client, admin_headers, sample_template):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    res_create = client.post(
        "/api/v1/mailings",
        headers=admin_headers,
        json={
            "title": "Запланированная кампания",
            "template_id": sample_template.id,
            "recipient_filter": {},
            "scheduled_at": future_time,
        },
    )
    assert res_create.status_code == status.HTTP_201_CREATED
    mailing_id = res_create.json()["id"]
    assert res_create.json()["status"] == MailingStatus.SCHEDULED.value

    # Cancel
    res_cancel = client.post(f"/api/v1/mailings/{mailing_id}/cancel", headers=admin_headers)
    assert res_cancel.status_code == status.HTTP_200_OK
    assert res_cancel.json()["status"] == MailingStatus.CANCELLED.value


def test_mailing_stats(client, admin_headers, sample_template):
    res_create = client.post(
        "/api/v1/mailings",
        headers=admin_headers,
        json={
            "title": "Кампания со статистикой",
            "template_id": sample_template.id,
            "recipient_filter": {},
        },
    )
    mailing_id = res_create.json()["id"]

    res_stats = client.get(f"/api/v1/mailings/{mailing_id}/stats", headers=admin_headers)
    assert res_stats.status_code == status.HTTP_200_OK
    data = res_stats.json()
    assert "delivery_rate_percent" in data
    assert "total_count" in data
