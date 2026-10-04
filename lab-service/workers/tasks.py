"""ARQ-задачи: чеки админу, уведомления пользователю, очистка временных файлов."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from aiogram import Bot

from backend.services.receipt_delivery import deliver_admin_receipt
from config.settings import get_settings

logger = logging.getLogger(__name__)


async def notify_user(ctx: dict, telegram_id: int, text: str) -> None:
    settings = get_settings()
    if not settings.user_bot_token:
        logger.warning("USER_BOT_TOKEN не задан — уведомление пропущено")
        return
    async with Bot(settings.user_bot_token) as bot:
        await bot.send_message(telegram_id, text)


async def notify_admin_receipt(
    ctx: dict, order_id: int, user_chat_id: int, user_message_id: int
) -> None:
    await deliver_admin_receipt(order_id, user_chat_id, user_message_id)


async def cleanup_temp_files(ctx: dict) -> None:
    settings = get_settings()
    temp_dir = settings.temp_dir
    if not temp_dir.exists():
        return
    cutoff = datetime.now(UTC) - timedelta(hours=settings.temp_ttl_hours)
    removed = 0
    for path in temp_dir.iterdir():
        if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) < cutoff:
            path.unlink(missing_ok=True)
            removed += 1
    logger.info("cleanup_temp_files removed=%s", removed)
