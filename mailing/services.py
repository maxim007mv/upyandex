# -*- coding: utf-8 -*-
"""Сервисы приложения: аутентификация, тариф, хранилище, управление рассылками.

Сервисы отделены от интерфейса: они не печатают ничего в консоль и не читают
``input()``. Это позволяет переиспользовать их в веб-версии (Django) без правок.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from .exceptions import AuthenticationError, ValidationError
from .models import Mailing, Status, User
from .senders import Sender


class Tariff:
    """Тариф отправки сообщений (сервис расчёта стоимости)."""

    def __init__(self, price_per_message: float) -> None:
        if price_per_message <= 0:
            raise ValidationError("цена за сообщение должна быть положительной")
        self._price_per_message = float(price_per_message)

    @property
    def price_per_message(self) -> float:
        return self._price_per_message

    def cost_for(self, recipient_count: int) -> float:
        """Стоимость рассылки для указанного числа получателей."""
        return round(recipient_count * self._price_per_message, 2)

    @staticmethod
    def format(amount: float) -> str:
        """Единый формат вывода суммы (как в ПР1: ``25.0``, ``2.5``)."""
        return str(round(amount, 2))

    @classmethod
    def standard(cls) -> Tariff:
        """Тариф по умолчанию: 2.5 руб. за сообщение."""
        return cls(2.5)


class AuthService:
    """Аутентификация пользователей по email и паролю."""

    def __init__(self, users: Iterable[User] = ()) -> None:
        self._users: list[User] = []
        for user in users:
            self.register(user)

    def register(self, user: User) -> None:
        """Добавить пользователя; email должен быть уникальным."""
        if not isinstance(user, User):
            raise ValidationError("можно зарегистрировать только пользователя")
        if any(existing.email == user.email for existing in self._users):
            raise ValidationError(
                f"пользователь с email {user.email} уже зарегистрирован"
            )
        self._users.append(user)

    @property
    def users(self) -> tuple[User, ...]:
        """Зарегистрированные пользователи (только чтение)."""
        return tuple(self._users)

    def login(self, email: str, password: str) -> User:
        """Вернуть пользователя при верных данных или возбудить исключение."""
        normalized_email = email.strip().lower()
        for user in self._users:
            if user.email == normalized_email and user.check_password(password):
                return user
        raise AuthenticationError("неверный email или пароль")

    def __len__(self) -> int:
        return len(self._users)


class MailingRepository:
    """Хранилище рассылок в памяти (паттерн «репозиторий»).

    Позже это место заменится на модели Django, а остальной код не изменится.
    """

    def __init__(self) -> None:
        self._mailings: list[Mailing] = []

    def add(self, mailing: Mailing) -> None:
        """Сохранить рассылку."""
        if not isinstance(mailing, Mailing):
            raise ValidationError("хранилище принимает только рассылки")
        self._mailings.append(mailing)

    def all(self) -> tuple[Mailing, ...]:
        """Все сохранённые рассылки (только чтение)."""
        return tuple(self._mailings)

    def __len__(self) -> int:
        return len(self._mailings)

    def __iter__(self) -> Iterator[Mailing]:
        return iter(self._mailings)

    def __contains__(self, mailing: object) -> bool:
        return mailing in self._mailings

    def __repr__(self) -> str:
        return f"MailingRepository(mailings={len(self._mailings)})"


class MailingService:
    """Бизнес-логика работы с рассылками.

    Композиция: сервис содержит хранилище, тариф и отправителя.
    Все зависимости передаются через конструктор (внедрение зависимостей),
    поэтому сервис легко тестировать и подменять.
    """

    def __init__(
        self,
        repository: MailingRepository,
        tariff: Tariff,
        sender: Sender,
    ) -> None:
        self._repository = repository
        self._tariff = tariff
        self._sender = sender

    @property
    def repository(self) -> MailingRepository:
        return self._repository

    @property
    def price_per_message(self) -> float:
        return self._tariff.price_per_message

    def create_draft(
        self,
        title: str,
        author: User,
        recipient_count: int,
    ) -> Mailing:
        """Создать черновик рассылки и сохранить его в хранилище."""
        mailing = Mailing(title=title, author=author, recipient_count=recipient_count)
        self._repository.add(mailing)
        return mailing

    def change_status(self, mailing: Mailing, status: Status) -> None:
        """Сменить статус рассылки."""
        mailing.change_status(status)

    def calculate_cost(self, mailing: Mailing) -> float:
        """Стоимость отправки рассылки по действующему тарифу."""
        return self._tariff.cost_for(len(mailing))

    def send(self, mailing: Mailing) -> int:
        """Отправить рассылку; вернуть число отправленных сообщений."""
        return mailing.send(self._sender)
