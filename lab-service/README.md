# Lab Service — Telegram-сервис лабораторных

Production-ready каркас для приёма заказов на лабораторные **ADS / PP1 / PP2**: оплата, файлы, GitHub, admin-проверка, статусы.

> **Статус:** архитектура и процессы готовы. Полная реализация handlers/services — следующий этап (сильная модель + токены).

## Mini App (`miniapp/`)

Статический клиент без сборки: `index.html`, `styles.css`, `app.js`, `config.js`, `catalog.js`. Можно хостить где угодно по HTTPS (GitHub Pages, Netlify, Cloudflare Pages) или через сам API по адресу `/app/`.

- **Вход** — по Telegram: клиент шлёт `initData` в заголовке `X-Telegram-Init-Data`, API проверяет подпись токеном бота и создаёт пользователя.
- **Доступы к предметам** — у каждого предмета своя ссылка на платформу; студент вводит логин/пароль, они сохраняются в его записи (`subject_credentials`, пароль зашифрован). Без доступа к предмету заказ по нему не создаётся.
- **Демо-режим** — если `apiBase` в `config.js` пустой: всё работает в браузере без сервера, бот и админ имитируются (чек → через 3 с «оплата подтверждена, работа началась»). Пароли в демо не сохраняются. Открыть: `miniapp/index.html` или любой статический хостинг.
- **Чек** — кнопка открывает `t.me/<bot>?start=receipt_<id>`, пользователь отправляет фото/PDF боту.

Процесс заказа:

```text
Mini App: выбор лаб → заказ (awaiting_payment)
Bot: чек → awaiting_review → уведомление админу с кнопками
Admin: ✅ → payment confirmed, заказ in_progress → уведомление пользователю
Admin: ❌ → заказ снова awaiting_payment, можно прислать новый чек
```

Для подключения к Telegram: задать `apiBase` и `botUsername` в `miniapp/config.js`, `MINIAPP_URL` в `.env`, и указать этот же URL в BotFather → Bot Settings → Menu Button.

## Документация

| Файл | Содержание |
|------|------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Компоненты, слои, эндпоинты |
| [docs/PROCESSES.md](docs/PROCESSES.md) | User flow, оплата, admin, worker |
| [docs/DATABASE.md](docs/DATABASE.md) | Таблицы, индексы, seed |
| [docs/SUPABASE.md](docs/SUPABASE.md) | Supabase: миграции, env, подключение |

## Быстрый старт

```bash
cd lab-service
cp .env.example .env
# заполнить токены когда будут

docker compose up -d postgres redis api worker
docker compose run --rm api python -m backend.database.seed
```

API: http://localhost:8000/docs

Боты (когда есть токены):

```bash
docker compose --profile bots up user-bot admin-bot
```

Локально без Docker:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

## Структура

```text
lab-service/
├── bot/                 # User + Admin Telegram bots
│   ├── handlers/
│   ├── keyboards/
│   ├── middlewares/
│   └── services/        # API client
├── backend/
│   ├── api/routes/      # FastAPI routers
│   ├── domain/          # OrderStatus, transitions
│   ├── models/          # SQLAlchemy ORM
│   ├── schemas/         # Pydantic DTO
│   └── services/        # Business logic (stubs)
├── workers/             # ARQ tasks
├── config/              # settings, labs catalog, file rules
├── storage/             # uploads + temp (volume)
└── docs/
```

## Что уже есть

- [x] Docker Compose (postgres, redis, api, worker, bots)
- [x] Модели БД + seed лабораторных из `config/labs.py`
- [x] Каталог API (`/catalog/subjects`, `/catalog/labs`)
- [x] FSM-состояния user-бота, admin middleware
- [x] Контракты сервисов, валидация файлов, статусы заказов
- [x] ARQ worker skeleton + cron cleanup

## TODO (следующая итерация)

- [ ] `OrderService` — полная реализация CRUD заказов
- [ ] Upload endpoints (multipart) + receipt flow
- [ ] User bot FSM до конца (лабы, языки, файлы, чек)
- [ ] Admin bot: карточки заказов, confirm/reject payment
- [ ] ARQ → реальная отправка Telegram
- [ ] Alembic migrations
- [ ] Rate limiting, webhook mode

## Безопасность

- Секреты только в `.env` (см. `.env.example`)
- Admin bot: middleware `AdminOnlyMiddleware`
- Admin API: заголовок `X-Admin-Telegram-Id`
- Bot → API: `X-Internal-Token`
- Пароли платформ **не** хранить; логи без секретов
