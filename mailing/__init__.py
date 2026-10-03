# -*- coding: utf-8 -*-
"""Система управления информационными рассылками (ООП-версия).

Пакет разделён на слои:

* :mod:`mailing.models` — доменные сущности (пользователь, рассылка, сообщение, статус);
* :mod:`mailing.services` — бизнес-логика (аутентификация, тариф, хранилище);
* :mod:`mailing.senders` — отправители сообщений;
* :mod:`mailing.ui` — консольный интерфейс;
* :mod:`mailing.exceptions` — собственные исключения;
* :mod:`mailing.config` — настройки.
"""

from .config import ADMIN_EMAIL, ADMIN_PASSWORD
from .exceptions import (
    AuthenticationError,
    MailingError,
    StateError,
    StorageError,
    ValidationError,
)
from .models import (
    Admin,
    Mailing,
    Message,
    MessageStatus,
    Operator,
    Status,
    User,
)
from .senders import ConsoleSender, Sender
from .services import AuthService, MailingRepository, MailingService, Tariff
from .storage import JsonStorage
from .ui import ConsoleUI

__version__ = "2.0.0"

__all__ = [
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
    "Admin",
    "AuthenticationError",
    "AuthService",
    "ConsoleSender",
    "ConsoleUI",
    "JsonStorage",
    "Mailing",
    "MailingError",
    "MailingRepository",
    "MailingService",
    "Message",
    "MessageStatus",
    "Operator",
    "Sender",
    "StateError",
    "Status",
    "StorageError",
    "Tariff",
    "User",
    "ValidationError",
]
