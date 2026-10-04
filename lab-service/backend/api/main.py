from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import admin, bot, catalog, health, miniapp
from config.settings import BASE_DIR, get_settings

MINIAPP_DIR: Path = BASE_DIR / "miniapp"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_storage_dirs()
    # Локальный запуск без Docker: создать таблицы и seed при старте.
    from backend.database.seed import seed_labs
    from backend.database.session import SessionLocal, engine
    from backend.models.base import Base

    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if "sqlite" in settings.database_url:
            for ddl in (
                "ALTER TABLE payments ADD COLUMN user_chat_id BIGINT",
                "ALTER TABLE payments ADD COLUMN user_message_id BIGINT",
            ):
                try:
                    await conn.execute(text(ddl))
                except Exception:
                    pass
    async with SessionLocal() as session:
        await seed_labs(session)
        await session.commit()
    yield


settings = get_settings()

app = FastAPI(
    title="Lab Service API",
    version="0.2.0",
    description="Backend для Telegram-сервиса лабораторных",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Telegram-Init-Data", "Bypass-Tunnel-Reminder"],
)

app.include_router(health.router)
app.include_router(catalog.router)
app.include_router(miniapp.router)
app.include_router(bot.router)
app.include_router(admin.router)

# Mini App можно отдавать отсюда же или с любого статического хостинга.
app.mount("/app", StaticFiles(directory=MINIAPP_DIR, html=True), name="miniapp")
