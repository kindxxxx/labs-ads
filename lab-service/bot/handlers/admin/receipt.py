"""Приём чека в @PAWS_CHECK_bot. Mini App: t.me/PAWS_CHECK_bot?start=r<order_id>."""

from __future__ import annotations

import re

import httpx
from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.services.api_client import ApiClient
from config.settings import Settings

router = Router(name="check_receipt")

DEEP_LINK = re.compile(r"^(?:r|receipt_)(\d+)$")
ORDER_TAG = re.compile(r"#(\d+)")


@router.message(CommandStart())
async def cmd_start(
    message: Message, command: CommandObject, state: FSMContext, settings: Settings
) -> None:
    if command.args and (m := DEEP_LINK.match(command.args)):
        order_id = int(m.group(1))
        await state.update_data(receipt_order_id=order_id)
        await message.answer(
            f"🧾 <b>Заказ #{order_id}</b>\n\n"
            "Переведите сумму на Kaspi и <b>отправьте сюда чек</b> — фото или PDF.\n"
            "Можно ответить на это сообщение скриншотом.",
            parse_mode="HTML",
        )
        return
    if message.from_user.id == settings.admin_id:
        await message.answer(
            "🐾 <b>PAWS CHECK</b> — бот проверки чеков.\n\n"
            "Клиенты присылают чеки сюда, тебе приходит копия с кнопками ✅ / ❌.",
            parse_mode="HTML",
        )
        return
    await message.answer(
        "🧾 Бот для отправки чеков PAWS.\n\n"
        "Откройте Mini App, оформите заказ и нажмите «Отправить чек» — "
        "ссылка подставит номер заказа автоматически."
    )


def _order_hint(message: Message, data: dict) -> int | None:
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
        if text and (m := ORDER_TAG.search(text)):
            return int(m.group(1))
    if message.caption and (m := ORDER_TAG.search(message.caption)):
        return int(m.group(1))
    return data.get("receipt_order_id")


@router.message(F.photo | F.document)
async def receive_receipt(message: Message, state: FSMContext, api: ApiClient) -> None:
    if message.photo:
        photo = message.photo[-1]
        kind, file_id, name, mime, size = (
            "photo", photo.file_id, "receipt.jpg", "image/jpeg", photo.file_size or 0
        )
    else:
        doc = message.document
        kind, file_id = "document", doc.file_id
        name = doc.file_name or "receipt"
        mime = doc.mime_type or "application/octet-stream"
        size = doc.file_size or 0

    try:
        order = await api.submit_receipt(
            {
                "telegram_id": message.from_user.id,
                "order_id": _order_hint(message, await state.get_data()),
                "telegram_file_id": file_id,
                "kind": kind,
                "original_name": name,
                "mime_type": mime,
                "size_bytes": size,
                "user_chat_id": message.chat.id,
                "user_message_id": message.message_id,
            }
        )
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", "ошибка сервера")
        except ValueError:
            detail = "ошибка сервера"
        await message.answer(f"❌ Не удалось принять чек: {detail}")
        return
    except httpx.HTTPError:
        await message.answer("⚠️ Сервис временно недоступен. Пришлите чек ещё раз через минуту.")
        return

    await state.update_data(receipt_order_id=None)
    await message.answer(
        f"✅ Чек по заказу #{order['id']} принят.\n"
        "Ожидайте подтверждения оплаты — уведомление придёт в @KBTUPaws_bot."
    )
