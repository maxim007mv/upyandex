#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Система управления информационными рассылками — ООП-версия.

Точка входа: собирает приложение из объектов и запускает консольный интерфейс.
Рассылки сохраняются в JSON-файле ``data/mailings.json`` и загружаются
при следующем запуске.

Запуск:
    python3 oop.py
"""

import sys
from pathlib import Path

from mailing import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    Admin,
    AuthService,
    ConsoleSender,
    ConsoleUI,
    JsonStorage,
    MailingError,
    MailingRepository,
    MailingService,
    Tariff,
)

#: Файл данных: рассылки сохраняются между запусками программы.
DATA_FILE = Path(__file__).resolve().parent / "data" / "mailings.json"


def build_application() -> ConsoleUI:
    """Собрать приложение из готовых объектов.

    Здесь создаются все зависимости: администратор, сервисы, хранилище,
    отправитель и интерфейс. Такой подход называют «корнем композиции»
    (composition root) — объекты не создают друг друга сами.
    """
    admin = Admin(ADMIN_EMAIL, ADMIN_PASSWORD)

    storage = JsonStorage(DATA_FILE)
    mailing_service = MailingService(
        repository=MailingRepository(storage.load()),
        tariff=Tariff.standard(),
        sender=ConsoleSender(),
        storage=storage,
    )

    return ConsoleUI(
        auth_service=AuthService([admin]),
        mailing_service=mailing_service,
    )


def main() -> int:
    """Запустить приложение; вернуть код выхода (0 — успех)."""
    try:
        application = build_application()
    except MailingError as error:
        print(f"Ошибка: {error}.")
        return 1
    return application.run()


if __name__ == "__main__":
    sys.exit(main())
