"""Доставка чека админу: copy_message внутри Check Bot — без скачивания."""

from __future__ import annotations

import logging

from aiogram import Bot

from backend.database.session import SessionLocal
from backend.domain.order_status import OrderStatus
from backend.services import orders as order_service
from bot.formatting import admin_order_keyboard, admin_order_text
from config.settings import get_settings

logger = logging.getLogger(__name__)

RECEIPT_NOT_DELIVERED = (
    "Чек получен, но не удалось сразу передать его на проверку. Пришлите чек ещё раз."
)


async def _notify_user(telegram_id: int, text: str) -> None:
    settings = get_settings()
    if not settings.user_bot_token:
        return
    async with Bot(settings.user_bot_token) as bot:
        await bot.send_message(telegram_id, text)


async def deliver_admin_receipt(
    order_id: int,
    user_chat_id: int,
    user_message_id: int,
) -> bool:
    """Копирует сообщение клиента админу тем же ботом, что принял чек."""
    settings = get_settings()
    if not settings.admin_bot_token or not settings.admin_id:
        logger.error("deliver_admin_receipt: ADMIN_BOT_TOKEN или ADMIN_ID не заданы")
        return False
    if not user_chat_id or not user_message_id:
        logger.error("deliver_admin_receipt: нет user_chat_id/user_message_id")
        return False

    async with SessionLocal() as session:
        order = await order_service.get_order(session, order_id)
        if order is None or order.status != OrderStatus.AWAITING_REVIEW:
            logger.warning(
                "deliver_admin_receipt: заказ %s не найден или статус %s",
                order_id,
                getattr(order, "status", None),
            )
            return False
        data = order_service.serialize_order(order, with_user=True)
        telegram_id = order.user.telegram_id

    caption = admin_order_text(data)
    keyboard = admin_order_keyboard(data)

    try:
        async with Bot(settings.admin_bot_token) as bot:
            sent = await bot.copy_message(
                chat_id=settings.admin_id,
                from_chat_id=user_chat_id,
                message_id=user_message_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
    except Exception:
        logger.exception("Не удалось скопировать чек админу, заказ %s", order_id)
        async with SessionLocal() as session:
            await order_service.revert_receipt(session, order_id)
            await session.commit()
        await _notify_user(telegram_id, RECEIPT_NOT_DELIVERED)
        return False

    async with SessionLocal() as session:
        await order_service.remember_admin_message(session, order_id, sent.chat.id, sent.message_id)
        await session.commit()

    await _notify_user(
        telegram_id,
        f"🟡 Чек по заказу #{order_id} на проверке. Ожидайте подтверждения оплаты.",
    )
    logger.info("Чек по заказу %s скопирован админу (msg %s)", order_id, sent.message_id)
    return True
