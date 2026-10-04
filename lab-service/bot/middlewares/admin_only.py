from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from config.settings import Settings


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self._admin_id = settings.admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None or user.id != self._admin_id:
            return None
        return await handler(event, data)
