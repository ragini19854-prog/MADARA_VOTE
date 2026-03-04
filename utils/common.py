from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus


def parse_channel_input(raw: str) -> tuple[str, int]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        raise ValueError("Invalid format")
    username, chat_id_s = parts
    if not username.startswith("@"):
        raise ValueError("Channel username must start with @")
    chat_id = int(chat_id_s)
    if not str(chat_id).startswith("-100"):
        raise ValueError("Channel id must start with -100")
    return username, chat_id


async def ensure_channel_membership(bot: Bot, channel_id: int, user_id: int) -> bool:
    member = await bot.get_chat_member(channel_id, user_id)
    return member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.RESTRICTED,
    }
