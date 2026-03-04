from aiogram.fsm.state import State, StatesGroup


class NewGiveawayState(StatesGroup):
    title = State()
    channel = State()
    mode = State()
    qr = State()
    stars_username = State()
    optional_image = State()
