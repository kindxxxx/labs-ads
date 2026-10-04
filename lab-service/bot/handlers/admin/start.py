"""Admin bot: /start для админа."""

from __future__ import annotations

import re

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

from config.settings import Settings

router = Router(name="admin_start")

DEEP_LINK = re.compile(r"^(?:r|receipt_)(\d+)$")


@router.message(CommandStart())
async def admin_start(message: Message, command: CommandObject, settings: Settings) -> None:
    if message.from_user.id != settings.admin_id:
        return
    if command.args and DEEP_LINK.match(command.args):
        return
    await message.answer(
        "🐾 <b>PAWS CHECK</b> — бот проверки чеков.\n\n"
        "Клиенты присылают чеки сюда, тебе приходит копия с кнопками ✅ / ❌.",
        parse_mode="HTML",
    )
