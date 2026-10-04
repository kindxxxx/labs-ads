"""Check Bot (@PAWS_CHECK_bot): приём чеков от клиентов + апрув админом."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers.admin import notifications, receipt
from bot.middlewares.admin_only import AdminOnlyMiddleware
from bot.services.api_client import ApiClient
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    if not settings.admin_bot_token:
        logger.error("ADMIN_BOT_TOKEN не задан")
        sys.exit(1)
    if not settings.admin_id:
        logger.error("ADMIN_ID не задан")
        sys.exit(1)

    bot = Bot(token=settings.admin_bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp["settings"] = settings
    dp["api"] = ApiClient(settings)

    # Клиенты шлют чеки; кнопки ✅/❌ — только админ.
    dp.callback_query.middleware(AdminOnlyMiddleware(settings))

    dp.include_router(receipt.router)
    dp.include_router(notifications.router)

    logger.info("Check bot starting (polling)…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
