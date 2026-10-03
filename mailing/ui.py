# -*- coding: utf-8 -*-
"""Консольный интерфейс — слой представления.

Интерфейс не создаёт объекты сам: сервисы передаются в конструктор
(внедрение зависимостей). Ввод и вывод — тоже параметры, поэтому интерфейс
легко заменить (например, на веб) или протестировать.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from .exceptions import MailingError, ValidationError
from .models import Mailing, Status, User
from .services import AuthService, MailingService, Tariff

#: Разделительная линия для заголовков.
LINE = "=" * 50


class ConsoleUI:
    """Диалог с пользователем в консоли."""

    def __init__(
        self,
        auth_service: AuthService,
        mailing_service: MailingService,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        self._auth_service = auth_service
        self._mailing_service = mailing_service
        self._input = input_func
        self._print = output_func

    # ---------- публичный метод ----------

    def run(self) -> int:
        """Выполнить полный сценарий; вернуть код выхода (0 — успех)."""
        self._print_header()

        try:
            user = self._login()
            mailing = self._create_mailing(user)
        except MailingError as error:
            self._print(f"Ошибка: {error}.")
            return 1

        self._print_summary(user, mailing)

        if mailing.can_send:
            self._mailing_service.send(mailing)
        else:
            self._print(f"Отправка сейчас не выполняется (статус: {mailing.status}).")

        self._print_mailings()
        self._print("\nРабота программы завершена.")
        return 0

    # ---------- шаги сценария ----------

    def _print_header(self) -> None:
        self._print(LINE)
        self._print("Система управления информационными рассылками")
        self._print("ООП-версия (классы, наследование, полиморфизм, JSON-хранилище)")
        self._print(LINE)

    def _login(self) -> User:
        self._print("\nВход в систему")
        email = self._ask("Email: ")
        password = self._ask("Пароль: ")
        user = self._auth_service.login(email, password)
        self._print("Вход выполнен успешно.")
        self._print(f"Дата входа: {datetime.now():%d.%m.%Y %H:%M}")
        return user

    def _create_mailing(self, author: User) -> Mailing:
        self._print("\n--- Создание черновика рассылки ---")
        title = Mailing.validate_title(self._ask("Название рассылки: "))
        recipient_count = self._ask_recipient_count()

        mailing = self._mailing_service.create_draft(title, author, recipient_count)
        self._print_cost(mailing)

        status = self._choose_status()
        self._mailing_service.change_status(mailing, status)
        return mailing

    def _ask_recipient_count(self) -> int:
        raw_count = self._ask("Сколько получателей запланировано (целое число): ")
        if not raw_count.isdigit():
            raise ValidationError("нужно ввести целое число")
        # Преобразование типов str -> int выполняется один раз и в одном месте.
        return int(raw_count)

    def _print_cost(self, mailing: Mailing) -> None:
        price = self._mailing_service.price_per_message
        total = self._mailing_service.calculate_cost(mailing)
        self._print("\nРасчёт стоимости (условно):")
        self._print(f"  Получателей: {len(mailing)}")
        self._print(f"  Цена за сообщение: {Tariff.format(price)} руб.")
        self._print(f"  Итого: {Tariff.format(total)} руб.")

    def _choose_status(self) -> Status:
        self._print("\nВыберите статус рассылки:")
        for number, status in Status.menu():
            self._print(f"  {number} — {status.value}")
        choice = self._ask("Номер: ")
        status = Status.from_menu_choice(choice)
        if status is None:
            self._print("Неизвестный пункт. Установлен статус ЧЕРНОВИК.")
            return Status.DRAFT
        return status

    def _print_summary(self, user: User, mailing: Mailing) -> None:
        self._print("\n" + LINE)
        self._print("Итог")
        self._print(LINE)
        self._print(f"Автор:       {user.email} ({user.role})")
        self._print(f"Рассылка:    {mailing.title}")
        self._print(f"Получателей: {len(mailing)}")
        self._print(f"Статус:      {mailing.status.value}")
        self._print(
            "Стоимость:   "
            f"{Tariff.format(self._mailing_service.calculate_cost(mailing))} руб."
        )
        self._print(f"Всего рассылок в системе: {len(self._mailing_service.repository)}")

    def _print_mailings(self) -> None:
        """Показать все сохранённые рассылки (обработка коллекции)."""
        mailings = self._mailing_service.repository.sorted_by_title()
        if not mailings:
            return
        self._print("\nРассылки в хранилище (по алфавиту):")
        for number, mailing in enumerate(mailings, start=1):
            self._print(f"  {number}. {mailing.title} — {mailing.status.value}")

    # ---------- служебные методы ----------

    def _ask(self, prompt: str) -> str:
        """Запросить строку и убрать лишние пробелы."""
        return self._input(prompt).strip()
