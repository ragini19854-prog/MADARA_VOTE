from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Settings
from database import Database
from keyboards.main_menu import main_menu_kb

router = Router(name="start")


def _intro_text(settings: Settings) -> str:
    return (
        "🎉 *Giveaway Management Bot*\n\n"
        "Run secure giveaways with deep links, membership checks, leaderboards, and paid vote approvals.\n\n"
        f"{settings.powered_by_text}\n"
        f"Support: {settings.support_link}"
    )


@router.message(CommandStart(deep_link=True))
async def start_deeplink(message: Message, command: CommandStart, db: Database, settings: Settings, state: FSMContext) -> None:
    await db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await state.clear()
    arg = command.args or ""
    if arg.startswith("giveaway_"):
        await message.answer("🔗 Processing giveaway link...")
        from handlers.giveaway import process_participation_link

        await process_participation_link(message, db, settings, int(arg.replace("giveaway_", "")))
        return
    await message.answer_photo(settings.banner_url, caption=_intro_text(settings), reply_markup=main_menu_kb(), parse_mode="Markdown")


@router.message(CommandStart())
async def start_root(message: Message, db: Database, settings: Settings, state: FSMContext) -> None:
    await db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await state.clear()
    await message.answer_photo(settings.banner_url, caption=_intro_text(settings), reply_markup=main_menu_kb(), parse_mode="Markdown")


@router.callback_query(F.data == "menu:root")
async def menu_root(callback: CallbackQuery, settings: Settings) -> None:
    await callback.message.edit_caption(caption=_intro_text(settings), reply_markup=main_menu_kb(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "menu:how_to_use")
async def how_to_use(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "1) Create giveaway\n2) Share deep link\n3) Participants join\n4) Subscribers vote\n5) Use manage panel to end and announce winner"
    )


@router.callback_query(F.data == "menu:donate")
async def donate(callback: CallbackQuery, settings: Settings) -> None:
    await callback.answer()
    await callback.message.answer_photo(settings.donate_qr, caption="💖 Thank you for supporting this project!")
