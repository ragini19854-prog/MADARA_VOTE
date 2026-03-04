from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message

from config import Settings
from database import Database
from keyboards.main_menu import (
    giveaway_mode_kb,
    manage_giveaway_kb,
    participant_vote_kb,
    participation_kb,
    payment_mode_kb,
)
from states.giveaway import NewGiveawayState
from states.payment import PaymentState
from utils.common import ensure_channel_membership, parse_channel_input

router = Router(name="giveaway")


@router.callback_query(F.data == "menu:new_giveaway")
async def new_giveaway(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(NewGiveawayState.title)
    await callback.answer()
    await callback.message.answer("📝 Enter Giveaway Title (short & helpful)")


@router.message(NewGiveawayState.title)
async def new_giveaway_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(NewGiveawayState.channel)
    await message.answer("Send channel username and ID\nFormat:\n@channelusername , -100xxxxxxxxxx")


@router.message(NewGiveawayState.channel)
async def new_giveaway_channel(message: Message, state: FSMContext) -> None:
    try:
        username, channel_id = parse_channel_input(message.text or "")
    except Exception:
        await message.answer("❌ Invalid format. Use: @channelusername , -100xxxxxxxxxx")
        return

    bot_member = await message.bot.get_chat_member(channel_id, message.bot.id)
    if bot_member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
        await message.answer("❌ Bot is not admin in this channel.")
        await state.clear()
        return
    if not getattr(bot_member, "can_post_messages", False) or not getattr(bot_member, "can_delete_messages", False):
        await message.answer("❌ Bot must have permission to post and delete messages.")
        await state.clear()
        return

    await state.update_data(channel_username=username, channel_id=channel_id)
    await state.set_state(NewGiveawayState.mode)
    await message.answer("Select giveaway mode:", reply_markup=giveaway_mode_kb())


@router.callback_query(NewGiveawayState.mode, F.data.startswith("newg:mode:"))
async def new_giveaway_mode(callback: CallbackQuery, state: FSMContext, db: Database, settings: Settings) -> None:
    mode = callback.data.rsplit(":", 1)[-1]
    await callback.answer()
    if mode == "paid":
        await state.update_data(mode="paid")
        await state.set_state(NewGiveawayState.qr)
        await callback.message.answer("Send QR image")
    else:
        data = await state.get_data()
        giveaway_id = await db.create_giveaway(
            host_id=callback.from_user.id,
            title=data["title"],
            channel_id=data["channel_id"],
            channel_username=data["channel_username"],
            mode="free",
            qr_file_id=None,
            stars_username=None,
        )
        link = f"https://t.me/{settings.bot_username}?start=giveaway_{giveaway_id}"
        await state.set_state(NewGiveawayState.optional_image)
        await state.update_data(giveaway_id=giveaway_id)
        await callback.message.answer(
            f"✅ Giveaway Created\nTitle: {data['title']}\nID: {giveaway_id}\nParticipation Link: {link}",
            reply_markup=manage_giveaway_kb(giveaway_id),
        )
        await callback.message.answer("Optional: upload giveaway image now, or type /skip")


@router.message(NewGiveawayState.qr, F.photo)
async def new_giveaway_qr(message: Message, state: FSMContext) -> None:
    await state.update_data(qr_file_id=message.photo[-1].file_id)
    await state.set_state(NewGiveawayState.stars_username)
    await message.answer("Send Telegram username for Stars")


@router.message(NewGiveawayState.stars_username)
async def new_giveaway_stars(message: Message, state: FSMContext, db: Database, settings: Settings) -> None:
    data = await state.get_data()
    stars_username = message.text.strip().lstrip("@")
    giveaway_id = await db.create_giveaway(
        host_id=message.from_user.id,
        title=data["title"],
        channel_id=data["channel_id"],
        channel_username=data["channel_username"],
        mode="paid",
        qr_file_id=data["qr_file_id"],
        stars_username=f"@{stars_username}",
    )
    link = f"https://t.me/{settings.bot_username}?start=giveaway_{giveaway_id}"
    await state.set_state(NewGiveawayState.optional_image)
    await state.update_data(giveaway_id=giveaway_id)
    await message.answer(
        f"✅ Giveaway Created\nTitle: {data['title']}\nID: {giveaway_id}\nParticipation Link: {link}",
        reply_markup=manage_giveaway_kb(giveaway_id),
    )
    await message.answer("Optional: upload giveaway image now, or type /skip")


@router.message(NewGiveawayState.optional_image, F.photo)
async def optional_image(message: Message, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    giveaway = await db.get_giveaway(data["giveaway_id"])
    await message.bot.send_photo(giveaway.channel_id, message.photo[-1].file_id, caption=f"🎉 {giveaway.title}\nJoin and vote now!")
    await state.clear()
    await message.answer("Image posted to channel and setup completed.")


@router.message(NewGiveawayState.optional_image, F.text == "/skip")
async def skip_optional_image(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Setup completed.")


async def process_participation_link(message: Message, db: Database, settings: Settings, giveaway_id: int) -> None:
    giveaway = await db.get_giveaway(giveaway_id)
    if not giveaway or giveaway.status != "active":
        await message.answer("❌ Giveaway not active.")
        return
    if not giveaway.participation_enabled:
        await message.answer("⛔ Participation is disabled for this giveaway.")
        return

    is_member = await ensure_channel_membership(message.bot, giveaway.channel_id, message.from_user.id)
    if not is_member:
        await message.answer(f"⚠️ Join {giveaway.channel_username} first, then try again.")
        return

    participant_id = await db.add_participant(giveaway_id, message.from_user.id, message.from_user.username)
    if participant_id is None:
        participant = await db.get_participant(giveaway_id, message.from_user.id)
        participant_id = participant["id"]
    else:
        ch_msg = await message.bot.send_message(
            giveaway.channel_id,
            f"🔥 PARTICIPANT DETAILS\nUsername: @{message.from_user.username or 'unknown'}\nUser ID: {message.from_user.id}",
            reply_markup=participant_vote_kb(giveaway_id, participant_id, 0),
        )
        await db.set_participant_post_message(participant_id, ch_msg.message_id)

    deep_link = f"https://t.me/{settings.bot_username}?start=giveaway_{giveaway_id}"
    await message.answer(
        "✅ Participation confirmed.",
        reply_markup=participation_kb(giveaway_id, bool(giveaway.paid_votes_enabled)),
    )
    await message.answer(f"Your link: {deep_link}")


@router.callback_query(F.data.startswith("vote:"))
async def vote_participant(callback: CallbackQuery, db: Database) -> None:
    _, giveaway_id_s, participant_id_s = callback.data.split(":")
    giveaway_id, participant_id = int(giveaway_id_s), int(participant_id_s)
    giveaway = await db.get_giveaway(giveaway_id)
    if not giveaway or giveaway.status != "active":
        await callback.answer("Giveaway not active.", show_alert=True)
        return
    if not await ensure_channel_membership(callback.bot, giveaway.channel_id, callback.from_user.id):
        await callback.answer("Only channel subscribers can vote.", show_alert=True)
        return
    ok = await db.add_vote(giveaway_id, participant_id, callback.from_user.id)
    if not ok:
        await callback.answer("You already voted for this participant.", show_alert=True)
        return

    count = await db.participant_votes(participant_id)
    try:
        await callback.message.edit_reply_markup(reply_markup=participant_vote_kb(giveaway_id, participant_id, count))
    except TelegramBadRequest:
        pass
    await callback.answer("Vote counted ✅")


@router.chat_member()
async def channel_member_update(event: ChatMemberUpdated, db: Database) -> None:
    if event.chat.type != "channel":
        return
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    if old_status in {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED} and new_status in {
        ChatMemberStatus.LEFT,
        ChatMemberStatus.KICKED,
    }:
        rows = await db.remove_votes_by_voter_for_channel(event.chat.id, event.from_user.id)
        for row in rows:
            count = await db.participant_votes(row["participant_id"])
            if row["post_message_id"]:
                try:
                    await event.bot.edit_message_reply_markup(
                        chat_id=event.chat.id,
                        message_id=row["post_message_id"],
                        reply_markup=participant_vote_kb(row["giveaway_id"], row["participant_id"], count),
                    )
                except TelegramBadRequest:
                    pass
            await event.bot.send_message(event.chat.id, "⚠️ Vote removed because user left the channel.")


@router.callback_query(F.data.startswith("giveaway:leaderboard:"))
async def leaderboard(callback: CallbackQuery, db: Database) -> None:
    gid = int(callback.data.split(":")[-1])
    board = await db.leaderboard(gid, limit=20)
    text = "🏆 Leaderboard\n\n" + "\n".join(
        f"{i+1}. @{r['username'] or r['user_id']} — {r['vote_count']}" for i, r in enumerate(board)
    )
    await callback.answer()
    await callback.message.answer(text if board else "No participants yet.")


@router.callback_query(F.data.startswith("giveaway:copy_link:"))
async def copy_link(callback: CallbackQuery, settings: Settings) -> None:
    gid = int(callback.data.split(":")[-1])
    await callback.answer()
    await callback.message.answer(f"https://t.me/{settings.bot_username}?start=giveaway_{gid}")


@router.callback_query(F.data.startswith("payment:start:"))
async def payment_start(callback: CallbackQuery, state: FSMContext) -> None:
    gid = int(callback.data.split(":")[-1])
    await state.set_state(PaymentState.choose_mode)
    await state.update_data(giveaway_id=gid)
    await callback.answer()
    await callback.message.answer("Choose payment mode:", reply_markup=payment_mode_kb(gid))


@router.callback_query(F.data.startswith("payment:mode:"))
async def payment_mode(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    _, _, mode, gid_s = callback.data.split(":")
    giveaway = await db.get_giveaway(int(gid_s))
    if not giveaway or not giveaway.paid_votes_enabled:
        await callback.answer("Paid votes disabled.", show_alert=True)
        return
    participant = await db.get_participant(giveaway.id, callback.from_user.id)
    if not participant:
        await callback.answer("Join giveaway first.", show_alert=True)
        return
    await state.update_data(mode=mode, participant_id=participant["id"])
    await state.set_state(PaymentState.screenshot)
    if mode == "money":
        await callback.message.answer_photo(giveaway.qr_file_id, caption="Send payment screenshot after scanning QR")
    else:
        await callback.message.answer(f"Send stars to {giveaway.stars_username} then upload screenshot")
    await callback.answer()


@router.message(PaymentState.screenshot, F.photo)
async def payment_screenshot(message: Message, state: FSMContext) -> None:
    await state.update_data(screenshot_file_id=message.photo[-1].file_id)
    await state.set_state(PaymentState.ref)
    await message.answer("Send UTR (money) or Stars transaction reference")


@router.message(PaymentState.ref)
async def payment_ref(message: Message, state: FSMContext) -> None:
    await state.update_data(ref=message.text.strip())
    await state.set_state(PaymentState.amount)
    await message.answer("Send amount / stars count (integer)")


@router.message(PaymentState.amount)
async def payment_amount(message: Message, state: FSMContext, db: Database) -> None:
    try:
        amount = int((message.text or "").strip())
    except ValueError:
        await message.answer("Amount must be integer")
        return
    data = await state.get_data()
    payment_id = await db.save_payment(
        giveaway_id=data["giveaway_id"],
        participant_id=data["participant_id"],
        payer_id=message.from_user.id,
        mode=data["mode"],
        screenshot_file_id=data["screenshot_file_id"],
        ref=data["ref"],
        amount=amount,
    )
    giveaway = await db.get_giveaway(data["giveaway_id"])
    owner_text = (
        f"💳 Payment Review\nID: {payment_id}\nMode: {data['mode']}\nFrom: {message.from_user.id}\n"
        f"Giveaway: {giveaway.id}\nParticipant: {data['participant_id']}\nRef: {data['ref']}\nAmount: {amount}"
    )
    kb = None
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"payment:approve:{payment_id}"),
                InlineKeyboardButton(text="❌ Deny", callback_data=f"payment:deny:{payment_id}"),
            ]
        ]
    )
    await message.bot.send_photo(giveaway.host_id, data["screenshot_file_id"], caption=owner_text, reply_markup=kb)
    await message.answer("Payment submitted for host approval.")
    await state.clear()


@router.callback_query(F.data.startswith("payment:approve:"))
async def payment_approve(callback: CallbackQuery, db: Database) -> None:
    pid = int(callback.data.split(":")[-1])
    await db.update_payment_status(pid, "approved", callback.from_user.id)
    await callback.answer("Approved. Host can now use /addvote <participant_id> <amount>")


@router.callback_query(F.data.startswith("payment:deny:"))
async def payment_deny(callback: CallbackQuery, db: Database) -> None:
    pid = int(callback.data.split(":")[-1])
    await db.update_payment_status(pid, "denied", callback.from_user.id)
    await callback.answer("Denied")


@router.callback_query(F.data.startswith("giveaway:stop_paid:"))
async def stop_paid(callback: CallbackQuery, db: Database) -> None:
    gid = int(callback.data.split(":")[-1])
    giveaway = await db.get_giveaway(gid)
    if not giveaway or giveaway.host_id != callback.from_user.id:
        await callback.answer("Host only", show_alert=True)
        return
    await db.update_giveaway_flags(gid, paid_votes_enabled=0)
    await callback.answer("Paid votes disabled")


@router.callback_query(F.data.startswith("giveaway:stop_part:"))
async def stop_part(callback: CallbackQuery, db: Database) -> None:
    gid = int(callback.data.split(":")[-1])
    giveaway = await db.get_giveaway(gid)
    if not giveaway or giveaway.host_id != callback.from_user.id:
        await callback.answer("Host only", show_alert=True)
        return
    await db.update_giveaway_flags(gid, participation_enabled=0)
    await callback.answer("Participation disabled")


@router.callback_query(F.data.startswith("giveaway:end:"))
async def end_giveaway(callback: CallbackQuery, db: Database) -> None:
    gid = int(callback.data.split(":")[-1])
    giveaway = await db.get_giveaway(gid)
    if not giveaway or giveaway.host_id != callback.from_user.id:
        await callback.answer("Host only", show_alert=True)
        return
    winner = await db.top_participant(gid)
    await db.update_giveaway_flags(gid, status="ended")
    if winner:
        await callback.bot.send_message(
            giveaway.channel_id,
            f"🏁 Giveaway ended. Winner: @{winner['username'] or winner['user_id']} with {winner['vote_count']} votes!",
        )
    await callback.answer("Giveaway ended")


@router.callback_query(F.data.startswith("giveaway:clear_posts:"))
async def clear_posts(callback: CallbackQuery, db: Database) -> None:
    gid = int(callback.data.split(":")[-1])
    giveaway = await db.get_giveaway(gid)
    if not giveaway or giveaway.host_id != callback.from_user.id:
        await callback.answer("Host only", show_alert=True)
        return
    ids = await db.clear_channel_posts(gid)
    for mid in ids:
        try:
            await callback.bot.delete_message(giveaway.channel_id, mid)
        except TelegramBadRequest:
            pass
    await callback.answer("Channel posts cleared")


@router.callback_query(F.data == "menu:my_giveaways")
async def my_giveaways(callback: CallbackQuery, db: Database) -> None:
    counts = await db.host_giveaway_counts(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(f"🎁 My Giveaways\nActive: {counts['active']}\nPast: {counts['past']}")
