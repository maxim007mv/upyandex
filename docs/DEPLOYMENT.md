# Руководство по развертыванию (Deployment Guide)

## 1. Быстрый запуск в Docker Compose (Рекомендуемый способ)

Для поднятия всего промышленного контура (FastAPI, PostgreSQL 15, Redis 7, Mailpit, Celery Worker, Celery Beat, Nginx + React SPA) достаточно одной команды:

```bash
docker compose up --build
```

### Доступные сервисы после старта:
| Сервис | Порт хоста | Назначение |
| :--- | :--- | :--- |
| **Frontend SPA** | `http://localhost:3008` | Веб-интерфейс администратора |
| **Backend API** | `http://localhost:8088` | REST API |
| **OpenAPI Docs** | `http://localhost:8088/docs` | Swagger UI документация |
| **Mailpit Web UI**| `http://localhost:8028` | Просмотр отправленных писем (локальный почтовый ящик) |
| **Mailpit SMTP** | `localhost:1028` | SMTP-шлюз для приема почты |
| **PostgreSQL** | `localhost:5439` | Основная база данных |
| **Redis** | `localhost:6389` | Брокер задач и распределенный кэш |

*Учетная запись администратора по умолчанию:*
- **Email:** `admin@example.com`
- **Пароль:** `admin123456`

---

## 2. Локальный запуск для разработки (Standalone)

Если вы хотите вести разработку локально без Docker:

### 2.1. Бэкенд
```bash
cd backend
source .venv/bin/activate
# Инициализация базы данных и сидирование данных
python -m app.db.init_db

# Запуск FastAPI сервера
uvicorn app.main:app --reload --port 8000
```

### 2.2. Фронтенд
```bash
cd frontend
npm run dev
# Открыть http://localhost:5173
```

---

## 3. Запуск автоматических тестов

Запуск полного набора автотестов (юнит-тесты, валидация синтаксиса, идемпотентность, воркеры):
```bash
cd backend
.venv/bin/pytest -v
```

Сборка фронтенда и проверка типов TypeScript:
```bash
cd frontend
npm run build
```
