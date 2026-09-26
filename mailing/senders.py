# -*- coding: utf-8 -*-
"""Отправители сообщений.

:class:`Sender` — абстрактный класс (абстракция + полиморфизм).
:class:`ConsoleSender` — учебная имитация: печатает отчёт в консоль.
В веб-версии появится, например, ``EmailSender`` с той же ролью.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from .models import Mailing


class Sender(ABC):
    """Абстрактный отправитель рассылки."""

    @abstractmethod
    def deliver(self, mailing: Mailing) -> None:
        """Выполнить доставку рассылки (реализуется наследниками)."""

    def __str__(self) -> str:
        return type(self).__name__


class ConsoleSender(Sender):
    """Имитация отправки с выводом отчёта в консоль."""

    def __init__(self, printer: Callable[[str], None] = print) -> None:
        self._print = printer

    def deliver(self, mailing: Mailing) -> None:
        self._print("Рассылка готова к отправке (имитация).")
        self._print(
            f"Сообщение: « {mailing.title} » будет отправлено "
            f"{mailing.recipient_count} получателям."
        )
