# -*- coding: utf-8 -*-
"""Собственные исключения предметной области.

Все исключения наследуются от :class:`MailingError`, поэтому вызывающий код
может перехватывать их одним блоком ``except MailingError``.
"""


class MailingError(Exception):
    """Базовое исключение системы управления рассылками."""


class ValidationError(MailingError):
    """Переданы некорректные данные (пустое название, отрицательное число и т. п.)."""


class AuthenticationError(MailingError):
    """Не удалось войти в систему (неверный email или пароль)."""


class StateError(MailingError):
    """Операция невозможна в текущем состоянии объекта."""
