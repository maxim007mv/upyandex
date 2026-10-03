# -*- coding: utf-8 -*-
"""Сервисы приложения: аутентификация, тариф, хранилище, управление рассылками.

Сервисы отделены от интерфейса: они не печатают ничего в консоль и не читают

"""

from __future__ import annotations

from typing import Iterable, Iterator

from .exceptions import AuthenticationError, ValidationError
from .models import Mailing, Status, User
from .senders import Sender
from .storage import JsonStorage


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

    def __init__(self, mailings: Iterable[Mailing] = ()) -> None:
        self._mailings: list[Mailing] = []
        for mailing in mailings:
            self.add(mailing)

    def add(self, mailing: Mailing) -> None:
        """Сохранить рассылку."""
        if not isinstance(mailing, Mailing):
            raise ValidationError("хранилище принимает только рассылки")
        self._mailings.append(mailing)

    def all(self) -> tuple[Mailing, ...]:
        """Все сохранённые рассылки (только чтение)."""
        return tuple(self._mailings)

    def search(self, query: str) -> tuple[Mailing, ...]:
        """Найти рассылки по подстроке названия (регистр не важен).

        Пустой запрос возвращает все рассылки — так работает поиск в ПР2.
        """
        query = query.strip().lower()
        if not query:
            return self.all()
        return tuple(
            mailing for mailing in self._mailings if query in mailing.title.lower()
        )

    def sorted_by_title(self) -> list[Mailing]:
        """Рассылки по алфавиту (без учёта регистра)."""
        return sorted(self._mailings, key=lambda mailing: mailing.title.lower())

    def sorted_by_date(self) -> list[Mailing]:
        """Рассылки по дате создания (сначала старые)."""
        return sorted(self._mailings)

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
        storage: JsonStorage | None = None,
    ) -> None:
        self._repository = repository
        self._tariff = tariff
        self._sender = sender
        self._storage = storage

    @property
    def repository(self) -> MailingRepository:
        return self._repository

    @property
    def price_per_message(self) -> float:
        return self._tariff.price_per_message

    def _persist(self) -> None:
        """Сохранить все рассылки на диск (если хранилище подключено).

        Вызывается после каждого изменения состояния, поэтому данные
        не теряются между запусками программы.
        """
        if self._storage is not None:
            self._storage.save(self._repository.all())

    def create_draft(
        self,
        title: str,
        author: User,
        recipient_count: int,
    ) -> Mailing:
        """Создать черновик рассылки и сохранить его в хранилище."""
        mailing = Mailing(title=title, author=author, recipient_count=recipient_count)
        self._repository.add(mailing)
        self._persist()
        return mailing

    def change_status(self, mailing: Mailing, status: Status) -> None:
        """Сменить статус рассылки."""
        mailing.change_status(status)
        self._persist()

    def calculate_cost(self, mailing: Mailing) -> float:
        """Стоимость отправки рассылки по действующему тарифу."""
        return self._tariff.cost_for(len(mailing))

    def send(self, mailing: Mailing) -> int:
        """Отправить рассылку; вернуть число отправленных сообщений."""
        sent_count = mailing.send(self._sender)
        self._persist()
        return sent_count
