"""FSM-состояния User Bot (мастер заказа)."""

from aiogram.fsm.state import State, StatesGroup


class OrderWizard(StatesGroup):
    choose_subject = State()
    choose_lab = State()
    choose_language = State()
    attach_materials = State()
    waiting_github_url = State()
    confirm_order = State()
    awaiting_receipt = State()
