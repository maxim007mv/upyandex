# -*- coding: utf-8 -*-
"""Тесты доменных сущностей (``mailing/models.py``).

Проверяются ООП-принципы: абстрактность, наследование, полиморфизм,
инкапсуляция, проверки данных и магические методы.
"""

import time
import unittest

from mailing import (
    Admin,
    Mailing,
    Message,
    MessageStatus,
    Operator,
    StateError,
    Status,
    User,
    ValidationError,
)
from mailing.senders import ConsoleSender


class UserTests(unittest.TestCase):
    """Пользователи: абстрактность, полиморфизм ролей, хеш пароля."""

    def test_user_is_abstract(self):
        with self.assertRaises(TypeError):
            User("user@example.com", "123")

    def test_roles_are_polymorphic(self):
        admin = Admin("Admin@Example.com", "123")
        operator = Operator("operator@example.com", "123")
        self.assertEqual(admin.role, "Администратор")
        self.assertEqual(operator.role, "Оператор")
        self.assertEqual(admin.email, "admin@example.com")

    def test_password_is_stored_as_hash(self):
        admin = Admin("admin@example.com", "secret")
        self.assertTrue(admin.check_password("secret"))
        self.assertFalse(admin.check_password("wrong"))
        self.assertNotIn("secret", str(admin.__dict__))

    def test_email_and_password_validation(self):
        with self.assertRaises(ValidationError):
            Admin("bad-email", "123")
        with self.assertRaises(ValidationError):
            Admin("a@b.ru", "1")

    def test_equality_by_email(self):
        self.assertEqual(Admin("a@b.ru", "123"), Admin("a@b.ru", "321"))
        self.assertNotEqual(Admin("a@b.ru", "123"), Operator("c@d.ru", "123"))


class StatusTests(unittest.TestCase):
    """Статусы рассылки: перечисление, отправка только из READY."""

    def test_only_ready_can_send(self):
        self.assertTrue(Status.READY.can_send)
        self.assertFalse(Status.DRAFT.can_send)
        self.assertFalse(Status.CANCELLED.can_send)
        self.assertFalse(Status.SENT.can_send)

    def test_menu_choices(self):
        self.assertIs(Status.from_menu_choice("1"), Status.DRAFT)
        self.assertIs(Status.from_menu_choice("2"), Status.READY)
        self.assertIs(Status.from_menu_choice("3"), Status.CANCELLED)
        self.assertIsNone(Status.from_menu_choice("9"))

    def test_menu_has_three_items_and_str(self):
        self.assertEqual(len(Status.menu()), 3)
        self.assertEqual(str(Status.DRAFT), "ЧЕРНОВИК")


class MessageTests(unittest.TestCase):
    """Сообщение: начальное состояние, отправка, равенство."""

    def setUp(self):
        self.message = Message("user1@example.com", "Новости")

    def test_initial_state(self):
        self.assertIs(self.message.status, MessageStatus.PENDING)
        self.assertIsNone(self.message.sent_at)

    def test_mark_sent_can_be_called_once(self):
        self.message.mark_sent()
        self.assertIs(self.message.status, MessageStatus.SENT)
        self.assertIsNotNone(self.message.sent_at)
        with self.assertRaises(StateError):
            self.message.mark_sent()

    def test_empty_recipient_is_rejected(self):
        with self.assertRaises(ValidationError):
            Message("   ", "Тема")

    def test_equality_and_str(self):
        self.assertEqual(self.message, Message("user1@example.com", "Новости"))
        self.assertIn("Новости", str(self.message))


class MailingTests(unittest.TestCase):
    """Рассылка: проверки, смена статуса, отправка, магические методы."""

    def setUp(self):
        self.author = Admin("author@example.com", "123")

    def test_creation_normalizes_input(self):
        mailing = Mailing("  Новости  ", self.author, 5)
        self.assertEqual(mailing.title, "Новости")
        self.assertIs(mailing.status, Status.DRAFT)
        self.assertEqual(len(mailing), 5)
        self.assertFalse(mailing.can_send)
        self.assertEqual(mailing.messages, ())

    def test_title_and_count_validation(self):
        for title, count in (("", 5), ("ok", 0), ("ok", -3), ("ok", 10_001)):
            with self.subTest(title=title, count=count):
                with self.assertRaises(ValidationError):
                    Mailing(title, self.author, count)

    def test_author_must_be_user(self):
        with self.assertRaises(ValidationError):
            Mailing("Новости", "строка", 5)

    def test_change_status(self):
        mailing = Mailing("Новости", self.author, 5)
        mailing.change_status(Status.CANCELLED)
        self.assertIs(mailing.status, Status.CANCELLED)
        with self.assertRaises(ValidationError):
            mailing.change_status("ЧЕРНОВИК")

    def test_send_requires_ready_status(self):
        mailing = Mailing("Новости", self.author, 2)
        with self.assertRaises(StateError):
            mailing.send(ConsoleSender(printer=lambda text: None))

    def test_send_creates_messages_and_locks_mailing(self):
        mailing = Mailing("Новости", self.author, 3)
        mailing.change_status(Status.READY)
        lines = []
        sent = mailing.send(ConsoleSender(printer=lines.append))
        self.assertEqual(sent, 3)
        self.assertIs(mailing.status, Status.SENT)
        self.assertIsNotNone(mailing.sent_at)
        self.assertEqual(len(mailing.messages), 3)
        self.assertEqual(len(list(mailing)), 3)
        self.assertEqual(len(lines), 2)
        with self.assertRaises(StateError):
            mailing.change_status(Status.DRAFT)

    def test_equality_and_sorting(self):
        first = Mailing("Первая", self.author, 1)
        time.sleep(0.002)
        second = Mailing("Вторая", self.author, 1)
        self.assertEqual(first, Mailing("Первая", self.author, 99))
        self.assertEqual(sorted([second, first]), [first, second])


if __name__ == "__main__":
    unittest.main()
