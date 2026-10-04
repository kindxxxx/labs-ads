"""User bot: мастер заказа — каркас FSM, логика TODO."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.user import subjects_keyboard
from bot.states import OrderWizard

router = Router(name="user_order_wizard")


@router.message(F.text == "📚 Новый заказ")
async def start_order(message: Message, state: FSMContext) -> None:
    await state.set_state(OrderWizard.choose_subject)
    await message.answer("Выбери предмет:", reply_markup=subjects_keyboard())


@router.callback_query(OrderWizard.choose_subject, F.data.startswith("subject:"))
async def on_subject_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    subject = callback.data.split(":", 1)[1]
    await state.update_data(subject=subject)
    await state.set_state(OrderWizard.choose_lab)
    # TODO: api.get_labs(subject) → labs_keyboard
    await callback.message.edit_text(
        f"Предмет: {subject}\n\nЗагрузка списка лабораторных… (TODO)"
    )
    await callback.answer()
