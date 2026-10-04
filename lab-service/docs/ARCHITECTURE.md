# Архитектура Telegram-сервиса лабораторных

## Обзор

Сервис для приёма заказов на лабораторные работы (ADS, PP1, PP2), загрузки материалов, ручной проверки оплаты и отслеживания статусов.

```
┌─────────────┐     ┌─────────────┐
│  User Bot   │     │  Admin Bot  │
│  (aiogram)  │     │  (aiogram)  │
└──────┬──────┘     └──────┬──────┘
       │    HTTP (internal)  │
       └──────────┬──────────┘
                  ▼
         ┌────────────────┐
         │   Backend API   │
         │   (FastAPI)     │
         └────────┬───────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
  PostgreSQL    Redis     Storage
                  │
                  ▼
            ┌──────────┐
            │  Worker  │
            │  (ARQ)   │
            └──────────┘
```

## Принципы

| Принцип | Решение |
|---------|---------|
| Разделение ботов | User и Admin — отдельные процессы, разные токены |
| Единый источник правды | Вся бизнес-логика в Backend API |
| Неблокирующий API | Уведомления, очистка файлов — через очередь |
| Расширяемость | Каталог лабораторных в БД + seed из конфига |
| Без секретов в коде | `.env`, `.env.example` без значений |

## Компоненты

### 1. User Bot (`bot/user_bot.py`)

- FSM-мастер заказа: предмет → лаба → язык → материалы → оплата
- Загрузка файлов (код, конспект, чек)
- Приём GitHub URL
- Просмотр статуса заказа
- **Не** ходит в БД напрямую — только через API

### 2. Admin Bot (`bot/admin_bot.py`)

- Middleware: доступ только для `ADMIN_ID`
- Уведомления о новых заказах и чеках
- Inline-кнопки: подтвердить / отклонить оплату
- Список заказов с фильтром по статусу
- Смена статуса, просмотр вложений

### 3. Backend API (`backend/`)

Слои:

```
api/routes/     → HTTP-контракт, валидация входа
services/       → бизнес-логика, смена статусов
repositories/   → доступ к БД (опционально, через SQLAlchemy)
models/         → ORM-сущности
schemas/        → Pydantic DTO
```

Эндпоинты (черновик):

| Method | Path | Назначение |
|--------|------|------------|
| GET | `/health` | Healthcheck |
| GET | `/catalog/subjects` | ADS / PP1 / PP2 |
| GET | `/catalog/labs` | Лабы по предмету |
| GET | `/catalog/labs/{id}` | Детали + языки + цена |
| POST | `/orders` | Создать заказ |
| GET | `/orders/{id}` | Заказ пользователя |
| GET | `/users/{telegram_id}/orders` | История заказов |
| POST | `/orders/{id}/attachments` | Загрузить файл |
| POST | `/orders/{id}/github` | Добавить GitHub URL |
| POST | `/orders/{id}/receipt` | Загрузить чек |
| POST | `/orders/{id}/submit` | Отправить на проверку |
| GET | `/admin/orders` | Список (admin) |
| PATCH | `/admin/orders/{id}/status` | Смена статуса |
| POST | `/admin/orders/{id}/payment/confirm` | Подтвердить оплату |
| POST | `/admin/orders/{id}/payment/reject` | Отклонить оплату |

Защита admin-роутов: заголовок `X-Admin-Token` или `X-Admin-Telegram-Id` (см. `config/settings.py`).

### 4. Worker (`workers/`)

Задачи ARQ (Redis):

| Задача | Триггер | Действие |
|--------|---------|----------|
| `notify_user_status_change` | Смена статуса | Сообщение в User Bot |
| `notify_admin_new_order` | Новый заказ / чек | Сообщение в Admin Bot |
| `cleanup_temp_files` | Cron / после обработки | Удаление просроченных файлов |
| `validate_attachment` | После upload | Проверка MIME, размера, антивирус (опц.) |

### 5. Storage (`storage/`)

- `storage/uploads/{order_id}/` — постоянные вложения
- `storage/temp/` — временные, TTL из конфига
- Volume в Docker: `./storage:/app/storage`

## Модель данных

См. `docs/DATABASE.md` и `backend/models/`.

Ключевые связи:

```
User 1──* Order *──1 Lab
Order 1──* Attachment
Order 1──* GithubLink
Order 1──* Payment
Order 1──* OrderStatusHistory
Order *──1 Language (nullable до выбора)
```

## Статусы заказа

```text
awaiting_payment   → Ожидает оплату
awaiting_review    → Ожидает проверки (чек загружен)
paid               → Оплачен
in_progress        → В работе
completed          → Готово
rejected           → Отклонён
```

Допустимые переходы — в `backend/domain/order_status.py`.

## Масштабирование (будущее)

- Webhook вместо polling для ботов
- S3 вместо локального storage
- Несколько admin-ID
- Автопроверка оплаты (Kaspi API)
- Личный кабинет (web)

## Что реализует следующая модель

- [ ] Полные handlers ботов (FSM, keyboards)
- [ ] Реализация всех API endpoints
- [ ] ARQ worker + отправка Telegram из worker
- [ ] Rate limiting (slowapi / redis)
- [ ] Alembic autogenerate + первый migrate
- [ ] Интеграционные тесты
- [ ] CI/CD
