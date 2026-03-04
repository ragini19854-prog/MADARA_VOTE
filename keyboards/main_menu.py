from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 New Giveaway", callback_data="menu:new_giveaway")],
            [InlineKeyboardButton(text="🎁 My Giveaways", callback_data="menu:my_giveaways")],
            [InlineKeyboardButton(text="📖 How To Use", callback_data="menu:how_to_use")],
            [InlineKeyboardButton(text="➕ Add Channel", callback_data="menu:add_channel")],
            [InlineKeyboardButton(text="➕ Add Group", callback_data="menu:add_group")],
            [InlineKeyboardButton(text="💖 Donate", callback_data="menu:donate")],
            [InlineKeyboardButton(text="📝 Create Post", callback_data="menu:create_post")],
        ]
    )


def giveaway_mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Paid Mode", callback_data="newg:mode:paid")],
            [InlineKeyboardButton(text="🎁 Non-Paid Mode", callback_data="newg:mode:free")],
        ]
    )


def manage_giveaway_kb(giveaway_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Leaderboard", callback_data=f"giveaway:leaderboard:{giveaway_id}")],
            [InlineKeyboardButton(text="🛑 Stop Paid Votes", callback_data=f"giveaway:stop_paid:{giveaway_id}")],
            [InlineKeyboardButton(text="🛑 Stop Participation", callback_data=f"giveaway:stop_part:{giveaway_id}")],
            [InlineKeyboardButton(text="🔚 End Giveaway", callback_data=f"giveaway:end:{giveaway_id}")],
            [InlineKeyboardButton(text="🗑 Clear Channel Posts", callback_data=f"giveaway:clear_posts:{giveaway_id}")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="menu:root")],
        ]
    )


def participation_kb(giveaway_id: int, paid_enabled: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📋 Copy Vote Link", callback_data=f"giveaway:copy_link:{giveaway_id}")],
        [InlineKeyboardButton(text="🏆 Leaderboard", callback_data=f"giveaway:leaderboard:{giveaway_id}")],
        [InlineKeyboardButton(text="🔁 Get Links Again", callback_data=f"giveaway:copy_link:{giveaway_id}")],
    ]
    if paid_enabled:
        rows.insert(1, [InlineKeyboardButton(text="💰 Buy Paid Votes", callback_data=f"payment:start:{giveaway_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def participant_vote_kb(giveaway_id: int, participant_id: int, count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🗳 Vote ({count})", callback_data=f"vote:{giveaway_id}:{participant_id}")]
        ]
    )


def payment_mode_kb(giveaway_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💵 Money Paid", callback_data=f"payment:mode:money:{giveaway_id}")],
            [InlineKeyboardButton(text="⭐ Stars Paid", callback_data=f"payment:mode:stars:{giveaway_id}")],
        ]
    )
