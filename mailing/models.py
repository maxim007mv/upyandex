# -*- coding: utf-8 -*-
"""Доменные сущности системы: пользователь, рассылка, сообщение, статус.

Модуль ничего не знает ни о консоли, ни о хранилище — только правила
предметной области. Состояние объектов закрыто (инкапсуляция) и доступно
снаружи через свойства ``@property``.
"""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Iterator

from .exceptions import StateError, ValidationError

if TYPE_CHECKING:  # импорт только для аннотаций — избегаем циклического импорта
    from .senders import Sender

#: Простейшая проверка email: «что-то@что-то.что-то», без пробелов.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Status(Enum):
    """Статус рассылки (сущность «Статус»)."""

    DRAFT = "ЧЕРНОВИК"
    READY = "ГОТОВА К ОТПРАВКЕ"
    CANCELLED = "ОТМЕНЕНА"
    SENT = "ОТПРАВЛЕНА"

    @property
    def can_send(self) -> bool:
        """Можно ли отправлять рассылку в этом статусе."""
        return self is Status.READY

    @classmethod
    def menu(cls) -> tuple[tuple[str, Status], ...]:
        """Пункты меню выбора статуса: пары (номер, статус)."""
        return (("1", cls.DRAFT), ("2", cls.READY), ("3", cls.CANCELLED))

    @classmethod
    def from_menu_choice(cls, choice: str) -> Status | None:
        """Вернуть статус по номеру пункта меню (или ``None``)."""
        for number, status in cls.menu():
            if number == choice:
                return status
        return None

    def __str__(self) -> str:
        return self.value


class MessageStatus(Enum):
    """Статус одного сообщения."""

    PENDING = "ОЖИДАЕТ ОТПРАВКИ"
    SENT = "ОТПРАВЛЕНО"

    def __str__(self) -> str:
        return self.value


class User(ABC):
    """Пользователь системы (сущность «Пользователь»).

    Абстрактный класс: «пользователя вообще» создать нельзя, можно только
    конкретную роль — администратора (:class:`Admin`) или оператора
    (:class:`Operator`). Пароль не хранится в открытом виде, только хеш.
    """

    #: Минимальная длина пароля.
    MIN_PASSWORD_LENGTH = 3

    def __init__(self, email: str, password: str) -> None:
        normalized_email = email.strip().lower()
        if not _EMAIL_PATTERN.match(normalized_email):
            raise ValidationError(f"некорректный email: {email!r}")
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                "пароль должен содержать не менее "
                f"{self.MIN_PASSWORD_LENGTH} символов"
            )
        self._email = normalized_email
        self._password_hash = self._hash_password(password)

    @property
    def email(self) -> str:
        """Email пользователя (только чтение)."""
        return self._email

    @property
    @abstractmethod
    def role(self) -> str:
        """Название роли; каждый наследник возвращает своё значение."""

    def check_password(self, password: str) -> bool:
        """Проверить пароль, не раскрывая сохранённый хеш."""
        return self._hash_password(password) == self._password_hash

    @staticmethod
    def _hash_password(password: str) -> str:
        """Необратимо преобразовать пароль (SHA-256)."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def __str__(self) -> str:
        return f"{self.role} <{self._email}>"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(email={self._email!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self._email == other._email

    def __hash__(self) -> int:
        return hash(self._email)

    def to_dict(self) -> dict:
        """Представить пользователя данными, пригодными для JSON."""
        return {
            "role": self.role,
            "email": self._email,
            "password_hash": self._password_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> User:
        """Восстановить пользователя из данных JSON (обратно к ``to_dict``)."""
        try:
            user_class = _USER_CLASSES_BY_ROLE[data["role"]]
            email = data["email"]
            password_hash = data["password_hash"]
        except KeyError as error:
            raise ValidationError("некорректные данные пользователя") from error
        # Объект создаётся в обход __init__: в JSON уже хранится готовый
        # хеш пароля, и повторно хешировать его нельзя.
        user = object.__new__(user_class)
        user._email = email
        user._password_hash = password_hash
        return user


class Admin(User):
    """Администратор — полный доступ к управлению рассылками."""

    @property
    def role(self) -> str:
        return "Администратор"


class Operator(User):
    """Оператор — роль для будущих версий (полиморфизм через :attr:`role`)."""

    @property
    def role(self) -> str:
        return "Оператор"


#: Сопоставление роли и класса: нужно для восстановления наследников из JSON.
_USER_CLASSES_BY_ROLE: dict[str, type[User]] = {
    "Администратор": Admin,
    "Оператор": Operator,
}


class Message:
    """Единица доставки одному получателю (сущность «Сообщение»)."""

    def __init__(self, recipient: str, subject: str) -> None:
        recipient = recipient.strip()
        if not recipient:
            raise ValidationError("не указан получатель сообщения")
        self._recipient = recipient
        self._subject = subject.strip()
        self._status = MessageStatus.PENDING
        self._sent_at: datetime | None = None

    @property
    def recipient(self) -> str:
        return self._recipient

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def status(self) -> MessageStatus:
        return self._status

    @property
    def sent_at(self) -> datetime | None:
        return self._sent_at

    def mark_sent(self) -> None:
        """Пометить сообщение как отправленное."""
        if self._status is MessageStatus.SENT:
            raise StateError("сообщение уже отправлено")
        self._status = MessageStatus.SENT
        self._sent_at = datetime.now()

    def __str__(self) -> str:
        return f"«{self._subject}» → {self._recipient} ({self._status})"

    def __repr__(self) -> str:
        return (
            f"Message(recipient={self._recipient!r}, "
            f"subject={self._subject!r}, status={self._status.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return (self._recipient, self._subject) == (other._recipient, other._subject)

    def __hash__(self) -> int:
        return hash((self._recipient, self._subject))

    def to_dict(self) -> dict:
        """Представить сообщение данными, пригодными для JSON."""
        return {
            "recipient": self._recipient,
            "subject": self._subject,
            "status": self._status.name,
            "sent_at": self._sent_at.isoformat() if self._sent_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        """Восстановить сообщение из данных JSON (обратно к ``to_dict``)."""
        message = cls(recipient=data["recipient"], subject=data["subject"])
        message._status = MessageStatus[data["status"]]
        sent_at = data.get("sent_at")
        message._sent_at = datetime.fromisoformat(sent_at) if sent_at else None
        return message


class Mailing:
    """Рассылка (сущность «Рассылка»).

    Композиция: рассылка «состоит из» сообщений (объекты :class:`Message`)
    и ссылается на автора (объект :class:`User`).
    """

    #: Верхняя граница числа получателей — защита от случайной опечатки.
    MAX_RECIPIENTS = 10_000

    def __init__(self, title: str, author: User, recipient_count: int) -> None:
        self._title = self.validate_title(title)
        if not isinstance(author, User):
            raise ValidationError("автором рассылки должен быть пользователь")
        self._author = author
        self._recipient_count = self._validate_recipient_count(recipient_count)
        self._status = Status.DRAFT
        self._created_at = datetime.now()
        self._sent_at: datetime | None = None
        self._messages: list[Message] = []

    # --- свойства (инкапсуляция: поля закрыты, доступ только на чтение) ---

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> User:
        return self._author

    @property
    def recipient_count(self) -> int:
        return self._recipient_count

    @property
    def status(self) -> Status:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def sent_at(self) -> datetime | None:
        return self._sent_at

    @property
    def messages(self) -> tuple[Message, ...]:
        """Отправленные сообщения (кортеж — изменить список нельзя)."""
        return tuple(self._messages)

    @property
    def can_send(self) -> bool:
        """Готова ли рассылка к отправке."""
        return self._status.can_send

    # --- проверка данных ---

    @staticmethod
    def validate_title(title: str) -> str:
        """Проверить и нормализовать название.

        Публичный метод: интерфейс вызывает его сразу после ввода, чтобы
        сообщить об ошибке, не задавая лишних вопросов.
        """
        title = title.strip()
        if not title:
            raise ValidationError("название не может быть пустым")
        return title

    @classmethod
    def _validate_recipient_count(cls, count: int) -> int:
        if not isinstance(count, int) or isinstance(count, bool):
            raise ValidationError("число получателей должно быть целым числом")
        if count <= 0:
            raise ValidationError("число получателей должно быть больше нуля")
        if count > cls.MAX_RECIPIENTS:
            raise ValidationError(
                f"число получателей не должно превышать {cls.MAX_RECIPIENTS}"
            )
        return count

    # --- изменение состояния ---

    def change_status(self, status: Status) -> None:
        """Сменить статус рассылки (отправленную менять нельзя)."""
        if not isinstance(status, Status):
            raise ValidationError("неизвестный статус рассылки")
        if self._status is Status.SENT:
            raise StateError("отправленную рассылку нельзя изменить")
        self._status = status

    def send(self, sender: Sender) -> int:
        """Имитировать отправку рассылки.

        Создаёт по одному сообщению на каждого получателя, помечает их
        отправленными и передаёт отчёт отправителю. Возвращает число
        отправленных сообщений.
        """
        if not self._status.can_send:
            raise StateError(
                f"нельзя отправить рассылку в статусе «{self._status.value}»"
            )
        self._messages = [
            Message(recipient=f"user{number:05d}@example.com", subject=self._title)
            for number in range(1, self._recipient_count + 1)
        ]
        for message in self._messages:
            message.mark_sent()
        self._status = Status.SENT
        self._sent_at = datetime.now()
        sender.deliver(self)
        return len(self._messages)

    # --- магические методы ---

    def __len__(self) -> int:
        """``len(mailing)`` — число получателей."""
        return self._recipient_count

    def __iter__(self) -> Iterator[Message]:
        """Итерация по отправленным сообщениям."""
        return iter(self._messages)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mailing):
            return NotImplemented
        return (self._title, self._author) == (other._title, other._author)

    def __hash__(self) -> int:
        return hash((self._title, self._author))

    def __lt__(self, other: Mailing) -> bool:
        """Сравнение по дате создания (для сортировки списка рассылок)."""
        if not isinstance(other, Mailing):
            return NotImplemented
        return self._created_at < other._created_at

    def __str__(self) -> str:
        return (
            f"Рассылка «{self._title}» "
            f"({self._status.value}, {self._recipient_count} получателей)"
        )

    def __repr__(self) -> str:
        return (
            f"Mailing(title={self._title!r}, author={self._author.email!r}, "
            f"recipient_count={self._recipient_count}, "
            f"status={self._status.value!r})"
        )

    def to_dict(self) -> dict:
        """Представить рассылку данными, пригодными для JSON."""
        return {
            "title": self._title,
            "author": self._author.to_dict(),
            "recipient_count": self._recipient_count,
            "status": self._status.name,
            "created_at": self._created_at.isoformat(),
            "sent_at": self._sent_at.isoformat() if self._sent_at else None,
            "messages": [message.to_dict() for message in self._messages],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Mailing:
        """Восстановить рассылку из данных JSON (обратно к ``to_dict``)."""
        mailing = cls(
            title=data["title"],
            author=User.from_dict(data["author"]),
            recipient_count=data["recipient_count"],
        )
        mailing._status = Status[data["status"]]
        mailing._created_at = datetime.fromisoformat(data["created_at"])
        sent_at = data.get("sent_at")
        mailing._sent_at = datetime.fromisoformat(sent_at) if sent_at else None
        mailing._messages = [
            Message.from_dict(item) for item in data.get("messages", [])
        ]
        return mailing
