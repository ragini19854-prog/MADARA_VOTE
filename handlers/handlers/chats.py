from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import CallbackQuery, Message

from database import Database

router = Router(name="chats")


@router.callback_query(F.data.in_({"menu:add_channel", "menu:add_group"}))
async def add_chat_prompt(callback: CallbackQuery) -> None:
    what = "channel" if callback.data.endswith("channel") else "group"
    await callback.answer()
    await callback.message.answer(
        f"Forward any message from the {what} where you are admin and this bot is admin. I will store it."
    )


@router.message(F.forward_from_chat)
async def save_forwarded_chat(message: Message, db: Database) -> None:
    chat = message.forward_from_chat
    if chat.type not in {"channel", "supergroup", "group"}:
        return
    member = await message.bot.get_chat_member(chat.id, message.from_user.id)
    if member.status not in {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR}:
        await message.answer("❌ You must be admin of that chat.")
        return

    await db.save_user_chat(message.from_user.id, chat.id, chat.title or str(chat.id), chat.username, chat.type)
    await message.answer(f"✅ Added {chat.type}: {chat.title}\nID: {chat.id}")
