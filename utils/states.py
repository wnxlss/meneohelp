from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_faq = State()
    waiting_block_user = State()
