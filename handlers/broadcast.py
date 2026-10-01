import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from config import OWNER_IDS
from firebase import get_all_users, record_broadcast, ensure_user, log_activity

def is_owner(uid):
    return uid in OWNER_IDS

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("👥 No users found in Firebase.")
        return

    reply = update.message.reply_to_message
    args = context.args or []
    mode = "broadcast"

    # /broadcast bot is accepted as an alias.
    if args and args[0].lower() == "bot":
        mode = "broadcast_bot"
        args = args[1:]

    if reply is None and not args:
        await update.message.reply_text(
            "📢 Broadcast use:\n\n"
            "1. Kisi message par reply karke /broadcast bhejo.\n"
            "2. Ya /broadcast Your message likho.\n"
            "3. /broadcast bot bhi supported alias hai."
        )
        return

    await update.message.reply_text(f"📢 Broadcasting to {len(users)} Firebase users...")

    success = 0
    failed = 0

    for uid, data in users.items():
        try:
            chat_id = int(uid)
            if reply:
                await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=update.effective_chat.id,
                    message_id=reply.message_id,
                )
            else:
                text = " ".join(args)
                await context.bot.send_message(chat_id=chat_id, text=text)
            success += 1
            log_activity(chat_id, "broadcast_received", {"type": mode})
        except Exception as e:
            failed += 1
            print(f"[broadcast] failed user={uid}: {type(e).__name__}: {e}")
        # Small pacing delay helps avoid Telegram flood limits.
        await asyncio.sleep(0.05)

    record_broadcast(len(users), success, failed, mode)
    await update.message.reply_text(
        "📢 <b>Broadcast completed</b>\n\n"
        f"👥 Total: {len(users)}\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}",
        parse_mode="HTML"
    )
