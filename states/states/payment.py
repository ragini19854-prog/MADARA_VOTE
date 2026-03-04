from aiogram.fsm.state import State, StatesGroup


class PaymentState(StatesGroup):
    choose_mode = State()
    screenshot = State()
    ref = State()
    amount = State()
