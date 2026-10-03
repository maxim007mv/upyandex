# -*- coding: utf-8 -*-
"""Тесты сервисов (``mailing/services.py``).

Проверяются тариф, аутентификация, хранилище и бизнес-логика рассылок.
"""

import unittest

from mailing import (
    Admin,
    AuthenticationError,
    AuthService,
    ConsoleSender,
    Mailing,
    MailingRepository,
    MailingService,
    Status,
    Tariff,
    ValidationError,
)


class TariffTests(unittest.TestCase):
    """Тариф: стандартная цена, расчёт, формат вывода."""

    def test_standard_tariff(self):
        tariff = Tariff.standard()
        self.assertEqual(tariff.price_per_message, 2.5)
        self.assertEqual(tariff.cost_for(10), 25.0)

    def test_format_matches_pr1(self):
        self.assertEqual(Tariff.format(25.0), "25.0")
        self.assertEqual(Tariff.format(2.5), "2.5")

    def test_price_must_be_positive(self):
        with self.assertRaises(ValidationError):
            Tariff(0)
        with self.assertRaises(ValidationError):
            Tariff(-1.0)


class AuthServiceTests(unittest.TestCase):
    """Аутентификация: нормализация email, ошибки, уникальность."""

    def setUp(self):
        self.admin = Admin("admin@example.com", "123")
        self.auth = AuthService([self.admin])

    def test_login_normalizes_email(self):
        user = self.auth.login("  ADMIN@Example.COM ", "123")
        self.assertIs(user, self.admin)

    def test_login_with_wrong_credentials(self):
        with self.assertRaises(AuthenticationError):
            self.auth.login("admin@example.com", "wrong")
        with self.assertRaises(AuthenticationError):
            self.auth.login("unknown@example.com", "123")

    def test_duplicate_email_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.auth.register(Admin("admin@example.com", "321"))

    def test_len(self):
        self.assertEqual(len(self.auth), 1)


class MailingRepositoryTests(unittest.TestCase):
    """Хранилище: добавление, перебор, проверка вхождения."""

    def setUp(self):
        self.repository = MailingRepository()
        self.mailing = Mailing("Новости", Admin("a@b.ru", "123"), 3)

    def test_add_and_iterate(self):
        self.repository.add(self.mailing)
        self.assertEqual(len(self.repository), 1)
        self.assertIn(self.mailing, self.repository)
        self.assertEqual(list(self.repository), [self.mailing])
        self.assertEqual(self.repository.all(), (self.mailing,))

    def test_rejects_foreign_objects(self):
        with self.assertRaises(ValidationError):
            self.repository.add("не рассылка")

    def test_search_by_title(self):
        self.repository.add(self.mailing)
        self.repository.add(Mailing("Акция", Admin("b@b.ru", "123"), 5))

        self.assertEqual(self.repository.search("нов"), (self.mailing,))
        self.assertEqual(len(self.repository.search("")), 2)
        self.assertEqual(self.repository.search("такой нет"), ())

    def test_sorted_by_title(self):
        second = Mailing("Акция", Admin("b@b.ru", "123"), 5)
        self.repository.add(self.mailing)
        self.repository.add(second)

        self.assertEqual(
            [mailing.title for mailing in self.repository.sorted_by_title()],
            ["Акция", "Новости"],
        )

    def test_sorted_by_date(self):
        # self.mailing создана раньше (в setUp), second — позже.
        second = Mailing("Акция", Admin("b@b.ru", "123"), 5)
        self.repository.add(second)
        self.repository.add(self.mailing)

        self.assertEqual(
            [mailing.title for mailing in self.repository.sorted_by_date()],
            ["Новости", "Акция"],
        )

    def test_can_load_initial_mailings(self):
        repository = MailingRepository([self.mailing])
        self.assertEqual(repository.all(), (self.mailing,))


class MailingServiceTests(unittest.TestCase):
    """Бизнес-логика: создание черновика, стоимость, статус, отправка."""

    def setUp(self):
        self.repository = MailingRepository()
        self.service = MailingService(
            repository=self.repository,
            tariff=Tariff.standard(),
            sender=ConsoleSender(printer=lambda text: None),
        )
        self.author = Admin("author@example.com", "123")

    def test_create_draft_saves_to_repository(self):
        mailing = self.service.create_draft("Новости", self.author, 10)
        self.assertIn(mailing, self.repository)
        self.assertEqual(self.service.calculate_cost(mailing), 25.0)
        self.assertEqual(self.service.price_per_message, 2.5)

    def test_change_status_and_send(self):
        mailing = self.service.create_draft("Новости", self.author, 2)
        self.service.change_status(mailing, Status.READY)
        self.assertTrue(mailing.can_send)
        self.assertEqual(self.service.send(mailing), 2)
        self.assertIs(mailing.status, Status.SENT)


if __name__ == "__main__":
    unittest.main()
