from datetime import datetime, timezone, timedelta
from html import escape

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import OWNER_IDS, ACTIVE_USER_DAYS, VIDEOS_PER_REQUEST, AUTO_DELETE_HOURS, VIDEO_COOLDOWN_MINUTES
from firebase import (
    get_sources, stats, get_all_users, get_user, get_activity, get_bot_enabled, set_bot_enabled,
)

async def bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    uid = update.effective_user.id
    args = [a.lower() for a in (context.args or [])]
    if not args or args[0] not in {"on", "off", "status"}:
        state = "ON" if get_bot_enabled() else "OFF"
        await update.message.reply_text(
            f"🤖 <b>Video Parsing: {state}</b>\n\n"
            "Use <code>/bot on</code> to enable video parsing.\n"
            "Use <code>/bot off</code> to pause video parsing.\n"
            "Use <code>/bot status</code> to check current status.", parse_mode="HTML"
        )
        return
    action = args[0]
    if action == "status":
        state = "ON" if get_bot_enabled() else "OFF"
        await update.message.reply_text(f"🤖 <b>Video Parsing: {state}</b>", parse_mode="HTML")
        return
    enabled = action == "on"
    set_bot_enabled(enabled)
    await update.message.reply_text(
        "✅ <b>Video Parsing ON</b>\nUsers can request videos now." if enabled else
        "⛔ <b>Video Parsing OFF</b>\nUsers will receive the localized pause message instead of videos.",
        parse_mode="HTML"
    )

def is_owner(uid):
    return uid in OWNER_IDS

def _fmt_user(uid, u):
    name = escape(u.get("full_name") or u.get("first_name") or "Unknown")
    username = f"@{escape(u.get('username'))}" if u.get("username") else "No username"
    return (
        f"👤 <b>{name}</b>\n"
        f"🆔 <code>{uid}</code> | {username}\n"
        f"📨 Requests: {int(u.get('videos_requested', 0) or 0)}\n"
        f"🎬 Delivered: {int(u.get('videos_sent', 0) or 0)}\n"
        f"🕐 Last active: {escape(str(u.get('last_activity', '—')))}"
    )



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner-only detailed admin command guide."""
    if not update.effective_user or not is_owner(update.effective_user.id):
        return

    text = (
        "👑 <b>ADMIN PANEL — FULL COMMAND GUIDE</b>\n\n"
        "🔐 <b>Access</b>\n"
        "• Ye commands sirf configured OWNER_IDS ke liye hain.\n"
        "• Normal users ko admin menu/button nahi dikhega.\n\n"

        "🏠 <b>ADMIN PANEL</b>\n"
        "<code>/admin</code> — Admin Panel open kare.\n"
        "<code>/help</code> — Ye complete admin command guide dikhaye.\n\n"        "🤖 <b>VIDEO PARSING CONTROL</b>\n"
        "<code>/bot on</code> — Video parsing ON kare.\n"
        "<code>/bot off</code> — Video parsing OFF kare; users ko localized pause message milega.\n"
        "<code>/bot status</code> — Current parsing status dekhe.\n\n"

        "📊 <b>STATISTICS</b>\n"
        "<code>/stats</code> — Total users, active users, requests, batches, delivered videos, failures, sources aur broadcast statistics.\n"
        "<code>/bots</code> — Compact statistics/dashboard alias.\n\n"

        "👥 <b>USER MANAGEMENT</b>\n"
        "<code>/user</code> — Firebase se users ki first page list.\n"
        "<code>/user 2</code> — Users ki second page.\n"
        "<code>/user 3</code> — Third page; isi tarah aage.\n"
        "<code>/activity USER_ID</code> — Kisi user ka detailed activity, language, consent, requests, delivered videos, failures, current position aur cooldown.\n\n"

        "📂 <b>SOURCE MANAGEMENT</b>\n"
        "<code>/source list</code> — Approved source channels/groups ki list.\n"
        "<code>/source add CHAT_ID TITLE</code> — Naya source add kare.\n"
        "Example: <code>/source add -1001234567890 My Channel</code>\n"
        "<code>/source remove CHAT_ID</code> — Existing source remove kare.\n"
        "Example: <code>/source remove -1001234567890</code>\n\n"

        "📢 <b>BROADCAST</b>\n"
        "<code>/broadcast</code> — Kisi message par reply karke sab Firebase users ko copy/send kare.\n"
        "<code>/broadcast Your message</code> — Text broadcast bheje.\n"
        "<code>/broadcast bot</code> — Broadcast ka supported alias.\n\n"

        "🎬 <b>USER VIDEO SYSTEM</b>\n"
        f"• Har successful request me <b>{VIDEOS_PER_REQUEST}</b> videos bheje jaate hain.\n"
        f"• Successful batch ke baad cooldown <b>{VIDEO_COOLDOWN_MINUTES} minutes</b> hai.\n"
        "• Videos source se Bot API ke through copy hote hain; server par video download nahi hota.\n"
        "• User ki position Firebase me save hoti hai, isliye restart ke baad progress retain hoti hai.\n\n"

        "🧹 <b>AUTO DELETE</b>\n"
        f"• Sent video cleanup setting: <b>{AUTO_DELETE_HOURS} hours</b>.\n"
        "• Cleanup records Firebase me maintain hote hain.\n\n"

        "🌐 <b>LANGUAGE</b>\n"
        "• User apni language Language button se change kar sakta hai.\n"
        "• Selected language Firebase me save hoti hai.\n"
        "• First-time users ki Telegram language detect karke supported language set ki ja sakti hai.\n\n"

        "⚙️ <b>COMMON WORKFLOW</b>\n"
        "1. <code>/source add CHAT_ID TITLE</code> se source add karo.\n"
        "2. <code>/source list</code> se verify karo.\n"
        "3. <code>/stats</code> se bot activity check karo.\n"
        "4. <code>/user</code> se users dekho.\n"
        "5. Kisi user ki problem ho to <code>/activity USER_ID</code> check karo.\n"
        "6. Announcement ke liye <code>/broadcast</code> use karo.\n\n"

        "💡 <b>QUICK COMMANDS</b>\n"
        "<code>/admin</code> • <code>/help</code> • <code>/stats</code> • <code>/user</code> • <code>/bots</code>\n"
        "<code>/activity USER_ID</code> • <code>/source list</code> • <code>/broadcast</code>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistics", callback_data="adm:stats"),
         InlineKeyboardButton("📂 Sources", callback_data="adm:sources")],
        [InlineKeyboardButton("👥 Users", callback_data="adm:users"),
         InlineKeyboardButton("📢 Broadcast Help", callback_data="adm:broadcast")],
    ])
    await update.message.reply_text(
        "👑 <b>ADMIN PANEL</b>\n\n"
        "Commands:\n"
        "/stats\n/user\n/activity USER_ID\n/broadcast (reply to message)\n"
        "/source add/remove/list",
        parse_mode="HTML", reply_markup=kb
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    s = stats()
    await update.message.reply_text(
        "📊 <b>FULL BOT STATISTICS</b>\n\n"
        f"👥 Total Users: <b>{s['users']}</b>\n"
        f"🟢 Active Users ({ACTIVE_USER_DAYS}d): <b>{s['active_users']}</b>\n\n"
        f"📨 Total Requests: <b>{s['requests']}</b>\n"
        f"📦 Successful Batches: <b>{s['batches']}</b>\n"
        f"🎬 Videos Delivered: <b>{s['videos_sent']}</b>\n"
        f"⚠️ Failed Requests: <b>{s['failed']}</b>\n\n"
        f"📂 Total Sources: <b>{s['sources']}</b>\n"
        f"✅ Enabled Sources: <b>{s['enabled_sources']}</b>\n\n"
        f"📢 Broadcast Runs: <b>{s['broadcasts']}</b>\n"
        f"📤 Broadcast Delivered: <b>{s['broadcast_sent']}</b>\n"
        f"❌ Broadcast Failed: <b>{s['broadcast_failed']}</b>\n\n"
        f"ℹ️ Active user = activity within the last {ACTIVE_USER_DAYS} days.",
        parse_mode="HTML"
    )

async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("👥 No users found in Firebase.")
        return
    items = list(users.items())
    # Optional /user page_number
    try:
        page = max(1, int(context.args[0])) if context.args else 1
    except Exception:
        page = 1
    per_page = 10
    start = (page - 1) * per_page
    chunk = items[start:start + per_page]
    if not chunk:
        await update.message.reply_text("📭 No users on this page.")
        return
    total_pages = (len(items) + per_page - 1) // per_page
    text = [f"👥 <b>USERS — Page {page}/{total_pages}</b>\n"]
    for uid, u in chunk:
        text.append(_fmt_user(uid, u))
    text.append("\nUse <code>/user 2</code> for the next page.")
    await update.message.reply_text("\n\n".join(text), parse_mode="HTML")

async def activity_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_owner(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /activity USER_ID")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return
    u = get_user(uid)
    if not u:
        await update.message.reply_text("❌ User not found in Firebase.")
        return

    cooldown = u.get("cooldown_until") or "No active cooldown"
    recent = get_activity(uid, 10)
    lines = [
        "🔎 <b>USER ACTIVITY</b>",
        "",
        f"👤 Name: <b>{escape(u.get('full_name') or 'Unknown')}</b>",
        f"🔖 Username: @{escape(u.get('username'))}" if u.get("username") else "🔖 Username: —",
        f"🆔 User ID: <code>{uid}</code>",
        f"🌐 Language: {escape(str(u.get('language', '—')))}",
        f"✅ Consent: {escape(str(u.get('consent', '—')))}",
        f"📅 Joined: {escape(str(u.get('joined_at', '—')))}",
        f"🕐 Last Active: {escape(str(u.get('last_activity', '—')))}",
        "",
        "📊 <b>VIDEO STATISTICS</b>",
        f"📨 Requests: {int(u.get('videos_requested', 0) or 0)}",
        f"📦 Successful Batches: {int(u.get('successful_requests', 0) or 0)}",
        f"🎬 Videos Delivered: {int(u.get('videos_sent', 0) or 0)}",
        f"❌ Video Failures: {int(u.get('videos_failed', 0) or 0)}",
        f"⚠️ Failed Requests: {int(u.get('failed_requests', 0) or 0)}",
        f"📍 Current Position: {int(u.get('position', 0) or 0)}",
        "",
        "⏱️ <b>COOLDOWN</b>",
        f"{escape(str(cooldown))}",
        "",
        "🕘 <b>LAST EVENTS</b>",
    ]
    if recent:
        for item in recent:
            details = item.get("details") or {}
            lines.append(f"• {escape(str(item.get('time','—')))} — {escape(str(item.get('event','—')))} {escape(str(details))}")
    else:
        lines.append("• No activity log yet.")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def bots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /bots is an owner-friendly compact dashboard alias.
    await stats_command(update, context)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_owner(q.from_user.id):
        return
    action = q.data.split(":", 1)[1]
    if action == "stats":
        s = stats()
        await q.message.reply_text(
            f"📊 <b>Statistics</b>\n\n"
            f"👥 Users: {s['users']}\n"
            f"🟢 Active: {s['active_users']}\n"
            f"📨 Requests: {s['requests']}\n"
            f"🎬 Sent: {s['videos_sent']}\n"
            f"📂 Sources: {s['sources']}\n"
            f"📢 Broadcasts: {s['broadcasts']}",
            parse_mode="HTML"
        )
    elif action == "sources":
        sources = get_sources()
        if not sources:
            await q.message.reply_text("📂 No approved sources.")
            return
        lines = ["📂 <b>Approved Sources</b>\n"]
        for sid, item in sources.items():
            lines.append(f"• <code>{sid}</code> — {escape(item.get('title',''))} — {escape(item.get('type',''))}")
        await q.message.reply_text("\n".join(lines), parse_mode="HTML")
    elif action == "users":
        users = get_all_users()
        await q.message.reply_text(f"👥 Firebase Users: <b>{len(users)}</b>\nUse /user to view pages.", parse_mode="HTML")
    elif action == "broadcast":
        await q.message.reply_text(
            "📢 <b>Broadcast</b>\n\n"
            "Reply to any message with <code>/broadcast</code>.\n"
            "Or use <code>/broadcast Your text here</code>.",
            parse_mode="HTML"
        )
