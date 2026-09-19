#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система управления информационными рассылками — начальная версия (ПР1).

python3 main.py
"""

# Импорт модулей (стандартная библиотека)
import sys
from datetime import datetime


# Учётные данные администратора (простые строки)
ADMIN_EMAIL = "lomakin2006@gmail.com"
ADMIN_PASSWORD = "123"


def main():
    print("=" * 50)
    print("Система управления информационными рассылками")
    print("Начальная версия (ПР1)")
    print("=" * 50)

    # --- Вход: строки, сравнение, ветвление ---
    print("\nВход в систему")
    email = input("Email: ").strip().lower()
    password = input("Пароль: ").strip()

    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        print("Ошибка: неверный email или пароль.")
        sys.exit(1)

    print("Вход выполнен успешно.")
    print("Дата входа:", datetime.now().strftime("%d.%m.%Y %H:%M"))

    # --- Сценарий: создание черновика рассылки ---
    print("\n--- Создание черновика рассылки ---")
    title = input("Название рассылки: ").strip()

    if title == "":
        print("Ошибка: название не может быть пустым.")
        sys.exit(1)

    # Преобразование типов: str -> int
    raw_count = input("Сколько получателей запланировано (целое число): ").strip()
    if not raw_count.isdigit():
        print("Ошибка: нужно ввести целое число.")
        sys.exit(1)

    recipient_count = int(raw_count)

    if recipient_count <= 0:
        print("Ошибка: число получателей должно быть больше нуля.")
        sys.exit(1)

    # Операции с числами
    # Стоимость условная: 2.5 руб. за одно сообщение
    price_per_message = 2.5
    total_cost = recipient_count * price_per_message

    # Преобразование float -> str для вывода
    print("\nРасчёт стоимости (условно):")
    print("  Получателей:", recipient_count)
    print("  Цена за сообщение:", str(price_per_message), "руб.")
    print("  Итого:", str(round(total_cost, 2)), "руб.")

    # Выбор статуса через ветвление
    print("\nВыберите статус рассылки:")
    print("  1 — ЧЕРНОВИК")
    print("  2 — ГОТОВА К ОТПРАВКЕ")
    print("  3 — ОТМЕНЕНА")
    choice = input("Номер: ").strip()

    if choice == "1":
        status = "ЧЕРНОВИК"
        can_send = False
    elif choice == "2":
        status = "ГОТОВА К ОТПРАВКЕ"
        can_send = True
    elif choice == "3":
        status = "ОТМЕНЕНА"
        can_send = False
    else:
        print("Неизвестный пункт. Установлен статус ЧЕРНОВИК.")
        status = "ЧЕРНОВИК"
        can_send = False

    # Итог сценария
    print("\n" + "=" * 50)
    print("Итог")
    print("=" * 50)
    print("Автор:     ", email)
    print("Рассылка:  ", title)
    print("Получателей:", recipient_count)
    print("Статус:    ", status)
    print("Стоимость: ", str(round(total_cost, 2)), "руб.")

    if can_send:
        print("\nРассылка готова к отправке (имитация).")
        print("Сообщение: «", title, "» будет отправлено", recipient_count, "получателям.")
    else:
        print("\nОтправка сейчас не выполняется (статус:", status + ").")

    print("\nРабота программы завершена.")


if __name__ == "__main__":
    main()
