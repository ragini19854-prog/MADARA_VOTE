from aiogram.fsm.state import State, StatesGroup


class BroadcastState(StatesGroup):
    message = State()
    confirm = State()


class AdminState(StatesGroup):
    waiting = State()
