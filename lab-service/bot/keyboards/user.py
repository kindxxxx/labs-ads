"""Клавиатуры User Bot — заглушки, реализация в следующей итерации."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config.labs import SUBJECTS


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📚 Новый заказ")
    builder.button(text="📋 Мои заказы")
    builder.button(text="ℹ️ Помощь")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def subjects_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.button(text=subject, callback_data=f"subject:{subject}")
    builder.adjust(3)
    return builder.as_markup()


def labs_keyboard(labs: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lab in labs:
        builder.button(
            text=f"Lab {lab['lab_number']} — {lab['price']} ₸",
            callback_data=f"lab:{lab['id']}",
        )
    builder.adjust(1)
    builder.button(text="◀️ Назад", callback_data="back:subject")
    return builder.as_markup()


def confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Создать заказ", callback_data=f"confirm:{order_id}"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )
