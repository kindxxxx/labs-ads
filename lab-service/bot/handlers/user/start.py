"""User bot: /start и кнопка открытия Mini App."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from bot.keyboards.user import main_menu
from config.settings import Settings

router = Router(name="user_start")


@router.message(CommandStart())
async def cmd_start(message: Message, settings: Settings) -> None:
    text = (
        "🐾 PAWS — заказ лабораторных ADS / PP1 / PP2.\n\n"
        "1. Выбери лабы в приложении\n"
        "2. Оплати на Kaspi и отправь чек сюда\n"
        "3. После подтверждения работа начнётся"
    )
    if settings.miniapp_url:
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🐾 Открыть PAWS", web_app=WebAppInfo(url=settings.miniapp_url))]
                ]
            ),
        )
    else:
        await message.answer(text, reply_markup=main_menu())
