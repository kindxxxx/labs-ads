# Supabase (PAWS)

Проект: **rslndrfinxxvpxcbcjkd**  
URL: https://rslndrfinxxvpxcbcjkd.supabase.co

## Что уже сделано

- Миграции в `supabase/migrations/`:
  - `20260928120000_paws_schema.sql` — таблицы PAWS
  - `20260928120100_paws_seed_labs.sql` — каталог лаб (ADS, PP1, PP2)
- Схема применена на remote Supabase (7 лаб, RLS включён).
- Backend читает `DATABASE_URL` или собирает URL из `SUPABASE_DB_PASSWORD`.

## Локальная настройка

1. В `.env` задай **Database password** из Supabase Dashboard → Settings → Database:
   ```
   SUPABASE_DB_PASSWORD=твой_пароль
   ```
2. Проверка подключения:
   ```bash
   cd lab-service
   .venv\Scripts\python.exe -m backend.database.seed
   ```
3. Supabase CLI (опционально):
   ```bash
   npm i -g supabase
   supabase login
   cd lab-service
   supabase link --project-ref rslndrfinxxvpxcbcjkd
   supabase db pull   # синхронизировать схему
   ```

## Env-переменные

| Переменная | Назначение |
|---|---|
| `SUPABASE_URL` | REST API URL |
| `SUPABASE_ANON_KEY` | публичный ключ (Mini App, если понадобится) |
| `SUPABASE_SERVICE_ROLE_KEY` | только backend / serverless, **не в браузер** |
| `SUPABASE_DB_PASSWORD` | пароль postgres для SQLAlchemy |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:...@db....supabase.co:5432/postgres` |

## Vercel (production)

**URL:** https://miniapp-sable-nine.vercel.app

API и Mini App на одном домене:
- `GET /health`
- `GET /miniapp/catalog`, `/miniapp/settings`, …
- `POST /api/telegram/check-webhook` — @PAWS_CHECK_bot

Env на Vercel: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `USER_BOT_TOKEN`, `ADMIN_BOT_TOKEN`, `ADMIN_ID`, `CREDENTIALS_KEY`, `TELEGRAM_WEBHOOK_SECRET`, …

Mini App: `demoMode: false`, `apiBase: ""` (same-origin).

## Безопасность

- `service_role` и `SUPABASE_DB_PASSWORD` — только на сервере.
- Таблицы PAWS с RLS без public policies: доступ через postgres/service connection backend'а.
