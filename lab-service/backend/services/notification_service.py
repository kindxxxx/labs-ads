"""Постановка уведомлений в очередь ARQ (API не ждёт Telegram)."""

from __future__ import annotations

import logging

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

logger = logging.getLogger(__name__)

_pool: ArqRedis | None = None


async def _get_pool(redis_url: str) -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(redis_url))
    return _pool


class NotificationService:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def _enqueue(self, job: str, *args) -> bool:
        if not self._redis_url or self._redis_url.startswith("skip:"):
            return False
        try:
            pool = await _get_pool(self._redis_url)
            await pool.enqueue_job(job, *args)
            return True
        except Exception:
            logger.warning("enqueue failed: %s — синхронная доставка", job)
            return False

    async def enqueue_user_message(self, telegram_id: int, text: str) -> bool:
        return await self._enqueue("notify_user", telegram_id, text)

    async def enqueue_admin_receipt(
        self, order_id: int, user_chat_id: int, user_message_id: int
    ) -> bool:
        return await self._enqueue(
            "notify_admin_receipt", order_id, user_chat_id, user_message_id
        )
