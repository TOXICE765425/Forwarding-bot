import asyncio
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes

from firebase import (
    ensure_user, get_user, update_user, set_position,
    get_pending_deletions, add_cleanup, remove_cleanup,
)
from config import VIDEOS_PER_REQUEST, AUTO_DELETE_HOURS


async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ <b>Help</b>\n\n"
        f"🎬 Video File — har click par {VIDEOS_PER_REQUEST} videos.\n"
        "🔁 Saare videos khatam hone ke baad sequence phir beginning se chalega.\n"
        f"🗑️ Sent videos {AUTO_DELETE_HOURS} hours ke baad automatically delete hote hain.\n"
        "📂 Videos configured Telegram sources se bot ke through copy hote hain."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML")


async def video_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    if (update.message.text or "").strip() != "🎬 Video File":
        return

    user = update.effective_user
    data = ensure_user(user)

    if data.get("consent") != "agree":
        await update.message.reply_text("❌ Please press Agree first.")
        return

    client = context.application.bot_data["source_client"]
    position = max(0, int(data.get("position", 0) or 0))

    await update.message.reply_text("🔎 Searching authorized sources...")
    update_user(
        user.id,
        {"videos_requested": int(data.get("videos_requested", 0)) + 1},
    )

    messages, total = await client.get_video_messages(
        position,
        VIDEOS_PER_REQUEST,
    )

    # User has reached the end: start the same source library again.
    if not messages and total > 0:
        position = 0
        messages, total = await client.get_video_messages(
            0,
            VIDEOS_PER_REQUEST,
        )
        if messages:
            set_position(user.id, 0)

    if not messages:
        await update.message.reply_text(
            "📭 Source channel me abhi koi video available nahi hai."
        )
        return

    try:
        # IMPORTANT: this uses Bot API copyMessage.
        # The video itself is never downloaded by Render.
        sent = await client.copy_messages_via_bot(
            context.bot,
            user.id,
            messages,
        )
    except Exception as e:
        update_user(
            user.id,
            {"failed_sends": int(data.get("failed_sends", 0)) + 1},
        )
        await update.message.reply_text(
            f"⚠️ Videos send nahi ho paye: {type(e).__name__}: {e}"
        )
        return

    if not sent:
        update_user(
            user.id,
            {"failed_sends": int(data.get("failed_sends", 0)) + 1},
        )
        await update.message.reply_text("⚠️ Videos copy nahi ho paaye.")
        return

    # Advance only by successfully copied messages.
    new_position = position + len(sent)

    # At the end, the next click will automatically wrap to position 0.
    set_position(user.id, new_position)

    latest = get_user(user.id)
    update_user(
        user.id,
        {"videos_sent": int(latest.get("videos_sent", 0)) + len(sent)},
    )

    # Keep the existing auto-delete feature for bot-side copies.
    delete_at = datetime.now(timezone.utc) + timedelta(hours=AUTO_DELETE_HOURS)
    for copied in sent:
        destination_message_id = getattr(copied, "message_id", None)
        if destination_message_id:
            add_cleanup(
                user.id,
                destination_message_id,
                destination_message_id,
                delete_at.isoformat(),
            )

    next_text = (
        "🔁 Next click par sequence beginning se chalega."
        if new_position >= total
        else f"📌 Next batch position: {new_position + 1}–{min(new_position + VIDEOS_PER_REQUEST, total)}"
    )

    await update.message.reply_text(
        f"✅ <b>{len(sent)} videos sent</b>\n"
        f"{next_text}\n"
        f"🗑️ Ye copies {AUTO_DELETE_HOURS} hours baad delete hongi.",
        parse_mode="HTML",
    )


async def auto_delete_worker(app):
    while True:
        try:
            pending = get_pending_deletions()
            now = datetime.now(timezone.utc)

            for uid, items in pending.items():
                if not isinstance(items, dict):
                    continue

                for mid, item in list(items.items()):
                    try:
                        delete_at = datetime.fromisoformat(item["delete_at"])
                        if delete_at <= now:
                            await app.bot.delete_message(
                                chat_id=int(uid),
                                message_id=int(item["message_id"]),
                            )
                            remove_cleanup(uid, mid)
                    except Exception:
                        remove_cleanup(uid, mid)
        except Exception as e:
            print("cleanup:", e)

        await asyncio.sleep(60)
