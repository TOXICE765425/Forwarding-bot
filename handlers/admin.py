from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import OWNER_IDS
from firebase import get_sources, add_source, remove_source, stats, get_user, update_user

def is_owner(uid):
    return uid in OWNER_IDS

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistics", callback_data="adm:stats"),
         InlineKeyboardButton("📂 Sources", callback_data="adm:sources")],
        [InlineKeyboardButton("👥 Users", callback_data="adm:users")],
    ])
    await update.message.reply_text("🔐 <b>Owner Panel</b>", parse_mode="HTML", reply_markup=kb)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_owner(q.from_user.id):
        return

    action = q.data.split(":", 1)[1]

    if action == "stats":
        s = stats()
        await q.message.reply_text(
            "📊 <b>Statistics</b>\n\n"
            f"👥 Users: {s['users']}\n"
            f"📂 Sources: {s['sources']}\n"
            f"🔢 Requests: {s['requests']}\n"
            f"🎬 Videos sent: {s['videos_sent']}\n"
            f"⚠️ Failed: {s['failed']}",
            parse_mode="HTML",
        )
    elif action == "sources":
        sources = get_sources()
        if not sources:
            await q.message.reply_text("📂 No approved sources.")
            return
        lines = ["📂 <b>Approved Sources</b>\n"]
        for sid, item in sources.items():
            lines.append(f"• <code>{sid}</code> — {item.get('title','')} — {item.get('type','')}")
        await q.message.reply_text("\n".join(lines), parse_mode="HTML")
    elif action == "users":
        s = stats()
        await q.message.reply_text(
            f"👥 Total users: <b>{s['users']}</b>\n"
            "Detailed user data is stored as metadata in Firebase.",
            parse_mode="HTML",
        )

async def source_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage:\n"
            "/source add -1001234567890 [title]\n"
            "/source remove -1001234567890\n"
            "/source list"
        )
        return

    action = args[0].lower()
    if action == "add" and len(args) >= 2:
        try:
            chat_id = int(args[1])
            title = " ".join(args[2:]) if len(args) > 2 else ""
            add_source(chat_id, title, "channel/group")
            await update.message.reply_text(f"✅ Source approved: {chat_id}")
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
    elif action == "remove" and len(args) >= 2:
        try:
            chat_id = int(args[1])
            remove_source(chat_id)
            await update.message.reply_text(f"✅ Source removed: {chat_id}")
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
    elif action == "list":
        sources = get_sources()
        if not sources:
            await update.message.reply_text("📂 No approved sources.")
            return
        text = "\n".join(f"{sid} — {v.get('title','')}" for sid, v in sources.items())
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("Unknown source command.")
