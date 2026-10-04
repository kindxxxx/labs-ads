from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def payment_review_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ ПОДТВЕРДИТЬ ОПЛАТУ", callback_data=f"pay_ok:{order_id}")],
            [InlineKeyboardButton(text="❌ НЕ ПОДТВЕРДИТЬ ОПЛАТУ", callback_data=f"pay_no:{order_id}")],
        ]
    )


def in_progress_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 ДОСТУПЫ К ПЛАТФОРМЕ", callback_data=f"creds:{order_id}")],
            [InlineKeyboardButton(text="✅ РАБОТА ГОТОВА", callback_data=f"done:{order_id}")],
        ]
    )
