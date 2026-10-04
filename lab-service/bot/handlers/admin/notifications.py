"""Admin bot: кнопки под сообщением с чеком. Решение редактирует это же сообщение."""

from __future__ import annotations

from html import escape

import httpx
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from bot.formatting import admin_order_keyboard, admin_order_text
from bot.services.api_client import ApiClient

router = Router(name="admin_notifications")


def _detail(exc: httpx.HTTPStatusError) -> str:
    try:
        return exc.response.json().get("detail", "Ошибка")
    except ValueError:
        return "Ошибка сервера"


async def _refresh_card(callback: CallbackQuery, order: dict) -> None:
    text = admin_order_text(order)
    keyboard = admin_order_keyboard(order)
    try:
        if callback.message.caption is not None:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except TelegramBadRequest as exc:
        # Повторное нажатие — содержимое не изменилось.
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.regexp(r"^(pay_ok|pay_no|done):\d+$"))
async def on_order_action(callback: CallbackQuery, api: ApiClient) -> None:
    action, raw_id = callback.data.split(":")
    order_id, admin_id = int(raw_id), callback.from_user.id
    try:
        if action == "done":
            order = await api.admin_complete(order_id, admin_id)
        else:
            order = await api.admin_payment_action(
                order_id, admin_id, "confirm" if action == "pay_ok" else "reject"
            )
    except httpx.HTTPStatusError as exc:
        await callback.answer(_detail(exc), show_alert=True)
        return

    await _refresh_card(callback, order)
    await callback.answer(
        {"pay_ok": "Оплата подтверждена", "pay_no": "Оплата отклонена", "done": "Заказ закрыт"}[action]
    )


@router.callback_query(F.data.regexp(r"^creds:\d+$"))
async def on_credentials(callback: CallbackQuery, api: ApiClient) -> None:
    order_id = int(callback.data.split(":")[1])
    try:
        creds = await api.admin_credentials(order_id, callback.from_user.id)
    except httpx.HTTPStatusError as exc:
        await callback.answer(_detail(exc), show_alert=True)
        return

    blocks = []
    for c in creds:
        head = f"<b>{escape(c['subject'])} Lab {c['lab_number']}</b> · #{c['contest_id']}"
        if not c.get("login"):
            blocks.append(f"{head}\n{escape(c.get('url') or '')}\n— логин не указан")
            continue
        blocks.append(
            f"{head}\n"
            f"<a href=\"{escape(c['url'])}\">{escape(c['url'])}</a>\n"
            f"Логин: <code>{escape(c['login'])}</code>\n"
            f"Пароль: <tg-spoiler>{escape(c.get('password') or '')}</tg-spoiler>"
        )
    await callback.message.reply(
        f"🔑 Доступы по заказу #{order_id}\n\n" + "\n\n".join(blocks), parse_mode="HTML"
    )
    await callback.answer()
