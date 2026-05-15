from aiogram.fsm.state import State, StatesGroup


class NewGiveawayState(StatesGroup):
    title = State()
    channel = State()
    giveaway_type = State()
    mode = State()
    payment_info = State()
    referral_setup = State()
    optional_image = State()


class ManageGiveawayState(StatesGroup):
    waiting = State()
