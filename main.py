#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Система управления информационными рассылками — ООП-версия.

Точка входа: собирает приложение из объектов и запускает консольный интерфейс.

Запуск:
    python3 main.py
"""

import sys

from mailing import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    Admin,
    AuthService,
    ConsoleSender,
    ConsoleUI,
    MailingError,
    MailingRepository,
    MailingService,
    Tariff,
)


def build_application() -> ConsoleUI:
    """Собрать приложение из готовых объектов.

    Здесь создаются все зависимости: администратор, сервисы, хранилище,
    отправитель и интерфейс. Такой подход называют «корнем композиции»
    (composition root) — объекты не создают друг друга сами.
    """
    admin = Admin(ADMIN_EMAIL, ADMIN_PASSWORD)

    mailing_service = MailingService(
        repository=MailingRepository(),
        tariff=Tariff.standard(),
        sender=ConsoleSender(),
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
