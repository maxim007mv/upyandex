# Notification & Mailing Management System

> **Масштабируемая, отказоустойчивая система управления информационными рассылками с асинхронной веерной отправкой и аналитикой статусов доставки в реальном времени.**

[![CI Pipeline](https://github.com/organization/mailing-system/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Ключевые возможности платформы

1. **Асинхронная веерная доставка (Worker Pattern):**
   - Пакетная разбивка очередей через **Celery** и брокер **Redis**.
   - Неблокирующий I/O: создание и планирование кампаний отвечает за $< 50$ мс.
   - Ограничение частоты отправки (**Rate Limiting**, до 20 писем/сек) во избежание спам-блокировок.

2. **Гарантия отказоустойчивости и идемпотентность:**
   - **Идемпотентность отправки:** составной уникальный ключ в базе исключает повторную отправку одного и того же письма адресату даже при падении воркеров.
   - **Exponential Backoff:** автоматический перезапуск упавших сообщений с прогрессивной задержкой (10с $\to$ 20с $\to$ 40с).
   - **Retry Failed:** возможность в 1 клик перезапустить отправку только тех сообщений, которые завершились ошибкой.

3. **Шаблонизация и валидация Jinja2:**
   - Богатая поддержка HTML и Markdown.
   - Автоматическое извлечение подстановочных переменных (`{{ user.full_name }}`, `{{ unsubscribe_url }}`).
   - Предварительная валидация синтаксиса до сохранения и **интерактивный предпросмотр** с произвольными тестовыми данными в реальном времени.

4. **Сегментация и работа с базой подписчиков:**
   - Сегментация по произвольным тегам (`vip`, `marketing`, `developers`).
   - Массовый импорт контактов из **CSV-файлов** с обработкой ошибок по строкам.
   - Полное соответствие требованиям почтовых служб: автоматическая подстановка заголовков `List-Unsubscribe` и публичная страница отписки в 1 клик по криптографически подписанному токену.

5. **Наблюдаемость и детальная аналитика:**
   - Дашборд с показателем доставляемости (**Delivery Rate %**), счетчиками статусов (`SENT`, `PENDING`, `FAILED`).
   - Real-time прогресс-бар активной отправки.
   - Поатомарный журнал доставки с причинами отказов почтовых серверов.

---

## 🛠 Технологический стек

| Слой | Технологии |
| :--- | :--- |
| **Backend** | Python 3.11, **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2**, Alembic, Jinja2, PyJWT, Bcrypt |
| **Очереди и задачи** | **Celery**, **Celery Beat** (периодический планировщик), **Redis 7** |
| **База данных** | **PostgreSQL 15** (production) / **SQLite** (локальный zero-config) |
| **Почтовый транспорт** | **Mailpit** (локальный dev-шлюз и Web UI) / SMTP (production) |
| **Frontend** | **React 19**, **TypeScript**, **Vite**, **Tailwind CSS**, Axios, Lucide Icons |
| **Инфраструктура** | **Docker**, **Docker Compose**, **Nginx**, GitHub Actions CI |
| **Тестирование** | **Pytest**, FastAPI TestClient, Mocking, 100% прохождение тест-сьюта |

---

## 🚀 Быстрый старт в 1 команду (Docker Compose)

Запустите весь стек (Postgres, Redis, Mailpit, FastAPI, Celery Worker, Celery Beat, Nginx + React):

```bash
docker compose up --build
```

### Адреса сервисов:
- **Веб-интерфейс администратора:** [http://localhost:3008](http://localhost:3008)
- **API Документация (Swagger UI):** [http://localhost:8088/docs](http://localhost:8088/docs)
- **Почтовый ящик Mailpit (Web UI):** [http://localhost:8028](http://localhost:8028)
- **REST API бэкенда:** [http://localhost:8088/api/v1](http://localhost:8088/api/v1)

### Данные для входа в панель:
- **Email:** `admin@example.com`
- **Пароль:** `admin123456`
*(На странице входа доступна кнопка «Заполнить» для мгновенного входа в 1 клик).*

---

## 💻 Локальный запуск без Docker

### 1. Бэкенд (FastAPI)
```bash
cd backend
source .venv/bin/activate

# Инициализация БД и создание тестовых данных
python -m app.db.init_db

# Запуск API сервера
uvicorn app.main:app --reload --port 8000
```

### 2. Фронтенд (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Откройте [http://localhost:5173](http://localhost:5173).

---

## 🧪 Запуск автотестов

Тестовый набор покрывает аутентификацию, CRUD подписчиков и шаблонов, CSV импорт, переходы состояний рассылки, идемпотентность и отказоустойчивость воркеров:

```bash
cd backend
.venv/bin/pytest -v
```

Сборка фронтенда:
```bash
cd frontend
npm run build
```

---

## 📂 Структура проекта

```text
├── .github/
│   └── workflows/
│       └── ci.yml                 # Непрерывная интеграция (CI)
├── docker-compose.yml             # Полный оркестратор всех сервисов
├── docker/
│   ├── backend.Dockerfile         # Образ FastAPI + Celery
│   ├── frontend.Dockerfile        # Multi-stage сборка Nginx + React
│   └── nginx.conf                 # Маршрутизация SPA и реверс-прокси
├── backend/
│   ├── app/
│   │   ├── api/                   # Эндпоинты (auth, subscribers, templates, mailings, stats)
│   │   ├── core/                  # Конфигурация (Pydantic Settings), безопасность (Bcrypt, JWT)
│   │   ├── db/                    # Модели SQLAlchemy (User, Template, Mailing, Delivery)
│   │   ├── schemas/               # Контракты Pydantic v2
│   │   ├── services/              # Бизнес-логика: EmailSenderService, MailingService, TemplateService
│   │   ├── workers/               # Celery воркеры, Beat планировщик, tasks (dispatch, send)
│   │   └── main.py                # Входная точка FastAPI
│   ├── alembic/                   # Миграции структуры БД
│   ├── tests/                     # 18 автоматических тестов (Pytest)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                   # Клиентские API модули
│   │   ├── components/            # UI компоненты (Layout, Navbar, Sidebar, StatCard, ProgressBar, Modal)
│   │   ├── pages/                 # Страницы (Dashboard, Mailings, Create Wizard, Detail, Users, Templates, Unsub)
│   │   ├── context/               # Контекст аутентификации (AuthContext)
│   │   └── types/                 # TypeScript типизация
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md            # Детальная архитектурная схема и описание конвейера
│   ├── API.md                     # Документация REST API
│   └── DEPLOYMENT.md              # Инструкция по развертыванию
├── README.md                      # Документация проекта
└── PROJECT_PLAN.md                # Исходный утвержденный план реализации
```

---

## 📄 Документация

- [Архитектура и системный дизайн](docs/ARCHITECTURE.md)
- [Спецификация REST API](docs/API.md)
- [Руководство по развертыванию](docs/DEPLOYMENT.md)
- [Архитектурный план проекта](PROJECT_PLAN.md)
