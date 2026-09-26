# -*- coding: utf-8 -*-
"""Тесты консольного интерфейса (``mailing/ui.py``).

Реальный ввод-вывод подменяется функциями из теста — это возможно
благодаря внедрению зависимостей в ``ConsoleUI``.
"""

import unittest

from mailing import (
    Admin,
    AuthService,
    ConsoleSender,
    ConsoleUI,
    MailingRepository,
    MailingService,
    Tariff,
)


class ConsoleUITests(unittest.TestCase):
    """Сценарии интерфейса без реальной консоли."""

    def run_ui(self, answers):
        """Прогнать интерфейс с заданными ответами; вернуть (код, вывод)."""
        output = []
        answers = iter(answers)
        ui = ConsoleUI(
            auth_service=AuthService([Admin("admin@example.com", "123")]),
            mailing_service=MailingService(
                repository=MailingRepository(),
                tariff=Tariff.standard(),
                sender=ConsoleSender(printer=output.append),
            ),
            input_func=lambda prompt: next(answers),
            output_func=output.append,
        )
        return ui.run(), "\n".join(output)

    def test_ready_mailing_is_sent(self):
        code, text = self.run_ui(
            ["admin@example.com", "123", "Новости недели", "10", "2"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Вход выполнен успешно.", text)
        self.assertIn("Итого: 25.0 руб.", text)
        self.assertIn("Статус:      ГОТОВА К ОТПРАВКЕ", text)
        self.assertIn("будет отправлено 10 получателям.", text)

    def test_draft_is_not_sent(self):
        code, text = self.run_ui(
            ["admin@example.com", "123", "Новости недели", "10", "1"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Отправка сейчас не выполняется", text)

    def test_unknown_menu_item_falls_back_to_draft(self):
        code, text = self.run_ui(
            ["admin@example.com", "123", "Новости недели", "10", "9"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Неизвестный пункт. Установлен статус ЧЕРНОВИК.", text)

    def test_wrong_password(self):
        code, text = self.run_ui(["admin@example.com", "wrong"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка: неверный email или пароль.", text)

    def test_empty_title(self):
        code, text = self.run_ui(["admin@example.com", "123", "   "])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка: название не может быть пустым.", text)

    def test_not_a_number(self):
        code, text = self.run_ui(["admin@example.com", "123", "Новости", "abc"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка: нужно ввести целое число.", text)

    def test_zero_recipients(self):
        code, text = self.run_ui(["admin@example.com", "123", "Новости", "0"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка: число получателей должно быть больше нуля.", text)

    def test_too_many_recipients(self):
        code, text = self.run_ui(["admin@example.com", "123", "Новости", "10001"])
        self.assertEqual(code, 1)
        self.assertIn("не должно превышать 10000", text)


if __name__ == "__main__":
    unittest.main()
