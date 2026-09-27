import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes
from firebase import ensure_user, get_user, update_user, set_position, get_pending_deletions, add_cleanup, remove_cleanup
from config import VIDEOS_PER_REQUEST, AUTO_DELETE_HOURS

async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ <b>Help</b>\n\n"
        "🎬 Video File — har request par 5 videos.\n"
        "🔢 Har user ka sequence alag rahega.\n"
        f"🗑️ Sent videos {AUTO_DELETE_HOURS} hours ke baad bot chat se automatically delete hote hain.\n"
        "📂 Videos configured Telegram sources se directly forward hote hain."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML")

async def video_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    text = (update.message.text or "").strip()
    if text == "ℹ️ Help":
        await help_button(update, context)
        return
    if text != "🎬 Video File":
        return

    user = update.effective_user
    data = ensure_user(user)
    if data.get("consent") != "agree":
        await update.message.reply_text("❌ Please press Agree first.")
        return

    client = context.application.bot_data["source_client"]
    position = int(data.get("position", 0))

    await update.message.reply_text("🔎 Searching authorized sources...")

    update_user(user.id, {"videos_requested": int(data.get("videos_requested", 0)) + 1})
    messages, total = await client.get_video_messages(position, VIDEOS_PER_REQUEST)

    if not messages:
        await update.message.reply_text(
            "📭 Abhi aur videos available nahi hain.\n"
            f"Current position: {position} / {total}"
        )
        return

    try:
        sent = await client.forward_to_user(user.id, messages)
    except Exception as e:
        update_user(user.id, {"failed_sends": int(data.get("failed_sends", 0)) + 1})
        await update.message.reply_text(f"⚠️ Videos send nahi ho paye: {e}")
        return

    new_position = position + len(messages)
    set_position(user.id, new_position)
    latest = get_user(user.id)
    update_user(user.id, {"videos_sent": int(latest.get("videos_sent", 0)) + len(sent)})

    delete_at = datetime.now(timezone.utc) + timedelta(hours=AUTO_DELETE_HOURS)
    for msg in sent:
        mid = getattr(msg, "id", None)
        if mid:
            add_cleanup(user.id, msg.id, mid, delete_at.isoformat())

    await update.message.reply_text(
        f"✅ <b>{len(sent)} videos sent</b>\n"
        f"📌 Next batch: {new_position + 1}–{new_position + VIDEOS_PER_REQUEST}\n"
        f"🗑️ Ye sent copies {AUTO_DELETE_HOURS} hours baad delete hongi.",
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
                            await app.bot.delete_message(chat_id=int(uid), message_id=int(item["message_id"]))
                            remove_cleanup(uid, mid)
                    except Exception:
                        # Message may already be deleted or inaccessible.
                        remove_cleanup(uid, mid)
        except Exception as e:
            print("cleanup:", e)
        await asyncio.sleep(60)
