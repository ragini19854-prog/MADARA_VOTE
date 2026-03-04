from aiogram.fsm.state import State, StatesGroup


class PostCreatorState(StatesGroup):
    photo = State()
    caption = State()
    buttons = State()
    confirm = State()
