"""Точка входа User Bot (polling). Требует USER_BOT_TOKEN в .env."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers.user import order_wizard, start
from bot.services.api_client import ApiClient
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    if not settings.user_bot_token:
        logger.error("USER_BOT_TOKEN не задан. Скопируй .env.example → .env")
        sys.exit(1)

    bot = Bot(token=settings.user_bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp["settings"] = settings
    dp["api"] = ApiClient(settings)

    dp.include_router(start.router)
    dp.include_router(order_wizard.router)

    logger.info("User bot starting (polling)…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
