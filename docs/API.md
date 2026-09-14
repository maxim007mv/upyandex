# Спецификация REST API (v1)

Интерактивная документация OpenAPI (Swagger UI) доступна по адресу:  
`http://localhost:8088/docs` (в Docker) или `http://localhost:8000/docs` (локально).

Базовый префикс всех маршрутов: `/api/v1`

---

## 1. Аутентификация (`/api/v1/auth`)

### 1.1. Вход в систему (JSON)
- **Метод:** `POST /api/v1/auth/login/json`
- **Тело запроса:**
```json
{
  "email": "admin@example.com",
  "password": "admin123456"
}
```
- **Ответ (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "full_name": "System Administrator",
    "role": "ADMIN",
    "is_active": true,
    "tags_attributes": ["admin"]
  }
}
```

### 1.2. Профиль текущего пользователя
- **Метод:** `GET /api/v1/auth/me`
- **Заголовки:** `Authorization: Bearer <token>`
- **Ответ (200 OK):** Объект `User`

---

## 2. Подписчики (`/api/v1/subscribers`)

### 2.1. Список подписчиков с фильтрацией
- **Метод:** `GET /api/v1/subscribers`
- **Параметры:**
  - `page` (int, default: 1)
  - `size` (int, default: 20)
  - `search` (string, поиск по email, имени, телефону)
  - `tag` (string, точное совпадение тега)
  - `is_active` (bool, true / false)

### 2.2. Добавление подписчика
- **Метод:** `POST /api/v1/subscribers`
- **Тело запроса:**
```json
{
  "email": "alex@company.com",
  "full_name": "Алексей Иванов",
  "phone": "+79991112233",
  "tags_attributes": ["vip", "marketing"],
  "is_active": true
}
```

### 2.3. Пакетный импорт из CSV
- **Метод:** `POST /api/v1/subscribers/import-csv`
- **Формат:** `multipart/form-data`, поле `file` (CSV с колонками: `email`, `full_name`, `phone`, `tags`)
- **Ответ (200 OK):**
```json
{
  "total_processed": 100,
  "added": 85,
  "updated": 15,
  "errors": []
}
```

### 2.4. Отписка по персональному токену (Public)
- **Метод:** `POST /api/v1/subscribers/unsubscribe-by-token`
- **Тело запроса:**
```json
{
  "token": "<unsubscribe_jwt_token>"
}
```

---

## 3. Шаблоны писем (`/api/v1/templates`)

### 3.1. Создание шаблона
- **Метод:** `POST /api/v1/templates`
- **Тело запроса:**
```json
{
  "title": "Приветственное письмо",
  "subject": "Добро пожаловать, {{ user.full_name }}!",
  "body_content": "<h2>Здравствуйте, {{ user.full_name }}!</h2><p>Ваш email: {{ user.email }}</p><a href=\"{{ unsubscribe_url }}\">Отписаться</a>"
}
```
*Автоматически валидирует синтаксис Jinja2 и извлекает переменные `["user.full_name", "user.email", "unsubscribe_url"]`.*

### 3.2. Предпросмотр рендера с тестовыми данными
- **Метод:** `POST /api/v1/templates/{id}/preview`
- **Тело запроса:**
```json
{
  "variables": {
    "user": {
      "full_name": "Дмитрий",
      "email": "dmitry@test.com"
    },
    "unsubscribe_url": "http://localhost:5173/unsubscribe?token=sample"
  }
}
```
- **Ответ (200 OK):**
```json
{
  "rendered_subject": "Добро пожаловать, Дмитрий!",
  "rendered_body": "<h2>Здравствуйте, Дмитрий!</h2>...",
  "detected_variables": ["unsubscribe_url", "user.email", "user.full_name"]
}
```

---

## 4. Кампании рассылок (`/api/v1/mailings`)

### 4.1. Создание рассылки
- **Метод:** `POST /api/v1/mailings`
- **Тело запроса:**
```json
{
  "title": "Маркетинговый анонс",
  "description": "Специальные предложения для VIP клиентов",
  "template_id": "<template_uuid>",
  "recipient_filter": {
    "is_active": true,
    "tags": ["vip"]
  },
  "scheduled_at": "2026-09-15T10:00:00Z"
}
```

### 4.2. Немедленный старт
- **Метод:** `POST /api/v1/mailings/{id}/start`
- Переводит статус в `PROCESSING`, генерирует записи доставки и передает задачи в очередь Celery.

### 4.3. Остановка / Отмена
- **Метод:** `POST /api/v1/mailings/{id}/cancel`
- Переводит статус в `CANCELLED`, останавливает отправку оставшихся сообщений.

### 4.4. Статистика выполнения
- **Метод:** `GET /api/v1/mailings/{id}/stats`
- **Ответ (200 OK):**
```json
{
  "mailing_id": "uuid",
  "title": "Маркетинговый анонс",
  "status": "COMPLETED",
  "total_count": 50,
  "success_count": 48,
  "failed_count": 2,
  "pending_count": 0,
  "delivery_rate_percent": 96.0,
  "started_at": "2026-09-14T11:00:00Z",
  "finished_at": "2026-09-14T11:00:05Z",
  "duration_seconds": 5.2
}
```

### 4.5. Журнал доставки сообщений
- **Метод:** `GET /api/v1/mailings/{id}/messages?status=FAILED`
- Возвращает детализацию по адресатам, статусам отправки (`SENT`, `PENDING`, `FAILED`) и сообщениям об ошибках.

### 4.6. Повторная отправка сбоев
- **Метод:** `POST /api/v1/mailings/{id}/retry-failed`
- Находит все сообщения в статусе `FAILED`, сбрасывает их в `PENDING` и отправляет на повторную доставку.
