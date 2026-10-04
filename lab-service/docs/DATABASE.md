# Схема базы данных (PostgreSQL)

## ER-диаграмма (логическая)

```text
users ──────< orders ──────< order_items >────── labs
                 │                                 │
                 │                                 └──< lab_languages >── languages
                 │
                 ├──< attachments
                 ├──< github_links
                 ├──< payments
                 └──< order_status_history
```

## Таблицы

### `users`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| telegram_id | BIGINT UNIQUE | ID в Telegram |
| username | VARCHAR(64) | @username |
| first_name | VARCHAR(128) | |
| last_name | VARCHAR(128) | |
| photo_url | VARCHAR(512) | Из Telegram initData |
| language_code | VARCHAR(8) | |
| created_at | TIMESTAMPTZ | |

Регистрации как таковой нет: пользователь создаётся/обновляется при первом открытии Mini App по подписанному Telegram `initData`.
| updated_at | TIMESTAMPTZ | |

### `subject_credentials`

Доступ студента к платформе предмета (ejudge). Студент указывает только логин/пароль; ссылки на контесты вычисляются как `CONTEST_ID_BASE[subject] + lab_number` в `config/labs.py`.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| user_id | FK → users | UNIQUE(user_id, subject) |
| subject | VARCHAR(8) | ADS, PP1, PP2 |
| login | VARCHAR(128) | |
| password_encrypted | TEXT | Fernet, ключ `CREDENTIALS_KEY` |
| created_at / updated_at | TIMESTAMPTZ | |

Пароль наружу не отдаётся никогда, кроме `GET /admin/orders/{id}/credentials` — и только для оплаченного заказа (`in_progress`/`paid`).

### `languages`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL PK | |
| name | VARCHAR(32) UNIQUE | Python, C++, … |

### `labs`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL PK | |
| subject | VARCHAR(8) | ADS, PP1, PP2 |
| lab_number | INT | Номер лабы |
| price | INT | Цена в ₸ |
| description | TEXT | |
| requirements | TEXT | |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

UNIQUE(subject, lab_number)

### `lab_languages`

| lab_id | FK → labs | |
| language_id | FK → languages | |

### `orders`

Один заказ = одна оплата. Выбранные лабы лежат в `order_items`.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| user_id | FK → users | |
| status | VARCHAR(32) | enum |
| total_price | INT | Сумма позиций на момент заказа |
| admin_comment | TEXT | Причина отклонения чека |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### `order_items`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| order_id | FK → orders | |
| lab_id | FK → labs | UNIQUE(order_id, lab_id) |
| language_id | FK → languages NULL | |
| price | INT | Снимок цены лабы |

### `attachments`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| order_id | FK → orders | |
| kind | VARCHAR(32) | code, receipt, notes, image, other |
| storage_path | VARCHAR(512) | Относительный путь |
| original_name | VARCHAR(256) | |
| mime_type | VARCHAR(128) | |
| size_bytes | BIGINT | |
| telegram_file_id | VARCHAR(256) | Для re-fetch из TG |
| created_at | TIMESTAMPTZ | |

### `github_links`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| order_id | FK → orders | |
| url | VARCHAR(2048) | |
| link_type | VARCHAR(16) | repo, file |
| created_at | TIMESTAMPTZ | |

### `payments`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| order_id | FK → orders UNIQUE | Один payment на заказ |
| amount | INT | Сумма к оплате |
| status | VARCHAR(16) | pending, confirmed, rejected |
| receipt_attachment_id | FK → attachments | Последний присланный чек |
| confirmed_by | BIGINT | telegram_id admin |
| confirmed_at | TIMESTAMPTZ | |
| rejection_reason | TEXT | |
| created_at | TIMESTAMPTZ | |

### `order_status_history`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGSERIAL PK | |
| order_id | FK → orders | |
| old_status | VARCHAR(32) | |
| new_status | VARCHAR(32) | |
| changed_by | BIGINT | telegram_id или 0=system |
| comment | TEXT | |
| created_at | TIMESTAMPTZ | |

## Индексы

- `orders(status, created_at DESC)` — admin-фильтры
- `orders(user_id, created_at DESC)` — история user
- `users(telegram_id)` — upsert при /start

## Seed

Скрипт `backend/database/seed.py` заполняет `labs` и `lab_languages` из `config/labs.py`.
