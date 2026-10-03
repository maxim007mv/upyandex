# -*- coding: utf-8 -*-
"""Тесты JSON-хранилища (pytest).

Проверяют, что рассылки сохраняются в файл и восстанавливаются при
следующем запуске, а ошибки файла не приводят к аварийному завершению
программы — вместо этого возбуждается понятное исключение ``StorageError``.
"""

import json

import pytest

from mailing import (
    Admin,
    ConsoleSender,
    JsonStorage,
    Mailing,
    MailingRepository,
    MailingService,
    Status,
    StorageError,
    Tariff,
)


def make_mailing(title="Новости недели", recipients=3):
    """Создать рассылку для тестов."""
    return Mailing(title, Admin("author@example.com", "123"), recipients)


def make_service(storage):
    """Создать сервис рассылок с указанным хранилищем."""
    return MailingService(
        repository=MailingRepository(),
        tariff=Tariff.standard(),
        sender=ConsoleSender(printer=lambda text: None),
        storage=storage,
    )


def test_missing_file_returns_empty_list(tmp_path):
    storage = JsonStorage(tmp_path / "mailings.json")
    assert storage.load() == []


def test_save_and_load_roundtrip(tmp_path):
    storage = JsonStorage(tmp_path / "mailings.json")
    mailing = make_mailing()
    storage.save([mailing])

    loaded = storage.load()
    assert len(loaded) == 1
    assert loaded[0].title == mailing.title
    assert loaded[0].author.email == mailing.author.email
    assert loaded[0].recipient_count == mailing.recipient_count
    assert loaded[0].author.check_password("123")


def test_sent_mailing_restores_status_and_messages(tmp_path):
    storage = JsonStorage(tmp_path / "mailings.json")
    mailing = make_mailing(recipients=2)
    mailing.change_status(Status.READY)
    mailing.send(ConsoleSender(printer=lambda text: None))
    storage.save([mailing])

    loaded = storage.load()[0]
    assert loaded.status is Status.SENT
    assert len(loaded.messages) == 2
    assert loaded.sent_at is not None


def test_corrupt_json_raises_storage_error(tmp_path):
    path = tmp_path / "mailings.json"
    path.write_text("{это не json", encoding="utf-8")
    with pytest.raises(StorageError):
        JsonStorage(path).load()


def test_wrong_structure_raises_storage_error(tmp_path):
    path = tmp_path / "mailings.json"
    path.write_text(json.dumps({"mailings": "нет"}), encoding="utf-8")
    with pytest.raises(StorageError):
        JsonStorage(path).load()


def test_service_saves_changes_to_disk(tmp_path):
    storage = JsonStorage(tmp_path / "mailings.json")
    service = make_service(storage)
    author = Admin("author@example.com", "123")

    mailing = service.create_draft("Новости", author, 5)
    service.change_status(mailing, Status.READY)

    saved = JsonStorage(storage.path).load()
    assert len(saved) == 1
    assert saved[0].status is Status.READY


def test_service_without_storage_works_in_memory():
    service = make_service(storage=None)
    mailing = service.create_draft("Новости", Admin("author@example.com", "123"), 5)
    assert service.repository.all() == (mailing,)
