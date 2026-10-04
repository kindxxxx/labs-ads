"""Карточка заказа в админ-боте. Одно сообщение (чек + данные) редактируется по мере смены статуса."""

from __future__ import annotations

from html import escape

from aiogram.types import InlineKeyboardMarkup

from bot.keyboards.admin import in_progress_keyboard, payment_review_keyboard

CAPTION_LIMIT = 1024

PAYMENT_LINE = {
    "pending": "⏳ Ожидает подтверждения",
    "confirmed": "✓ Подтверждена",
    "rejected": "✕ Не подтверждена — ждём новый чек",
}

ORDER_LINE = {
    "awaiting_payment": "⏳ Ожидает оплату",
    "awaiting_review": "⏳ Чек на проверке",
    "paid": "✓ Оплачен",
    "in_progress": "🔵 В работе",
    "completed": "✅ Готово",
    "rejected": "✕ Отклонён",
}


def _fmt_money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₸"


def _item_line(item: dict) -> str:
    lang = f" ({escape(item['language'])})" if item.get("language") else ""
    cid = item.get("contest_id")
    tag = f" · #{cid}" if cid else ""
    return f"• {item['subject']} Lab {item['lab_number']}{lang}{tag} — {_fmt_money(item['price'])}"


def admin_order_text(order: dict) -> str:
    user = order.get("user") or {}
    handle = f"@{user['username']}" if user.get("username") else f"id {user.get('telegram_id', '?')}"
    items = "\n".join(_item_line(i) for i in order["items"])
    lines = [
        f"<b>ЗАКАЗ #{order['id']}</b>",
        "",
        "<b>Состав:</b>",
        items,
        "",
        f"<b>Сумма:</b> {_fmt_money(order['total_price'])}",
        f"<b>Telegram:</b> {escape(handle)}",
    ]
    if order.get("user_message_id"):
        lines.append(f"<b>Чек клиента:</b> msg #{order['user_message_id']}")
    if order.get("admin_message_id"):
        lines.append(f"<b>Проверка:</b> msg #{order['admin_message_id']}")
    lines.extend([
        "",
        f"<b>Оплата:</b> {PAYMENT_LINE.get(order.get('payment_status'), '—')}",
        f"<b>Статус:</b> {ORDER_LINE.get(order['status'], order['status'])}",
    ])
    if order.get("admin_comment") and order.get("payment_status") == "rejected":
        lines.append(f"<b>Причина:</b> {escape(order['admin_comment'])}")
    return "\n".join(lines)[:CAPTION_LIMIT]


def admin_order_keyboard(order: dict) -> InlineKeyboardMarkup | None:
    if order["status"] == "awaiting_review":
        return payment_review_keyboard(order["id"])
    if order["status"] == "in_progress":
        return in_progress_keyboard(order["id"])
    return None
