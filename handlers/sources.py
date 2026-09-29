from telegram import Update
from telegram.ext import ContextTypes

from config import OWNER_IDS
from database import get_sources, add_source, remove_source


def _is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def _format_sources(sources):
    if not sources:
        return "📭 No approved sources found."

    lines = ["📚 Approved Sources", ""]

    for chat_id, data in sources.items():
        if not isinstance(data, dict):
            continue

        title = data.get("title") or "Unknown"
        chat_type = data.get("type") or "unknown"
        enabled = data.get("enabled", True)

        status = "✅ Enabled" if enabled else "❌ Disabled"

        lines.append(
            f"• {title}\n"
            f"  ID: `{chat_id}`\n"
            f"  Type: {chat_type}\n"
            f"  Status: {status}\n"
        )

    return "\n".join(lines)


async def source_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not user or not _is_owner(user.id):
        await update.message.reply_text(
            "❌ You are not authorized to use this command."
        )
        return

    args = context.args

    if not args:
        await update.message.reply_text(
            "📌 Source Management\n\n"
            "Use:\n"
            "/source add <chat_id> <title>\n"
            "/source remove <chat_id>\n"
            "/source list\n\n"
            "Examples:\n"
            "`/source add -1001234567890 My Channel`\n"
            "`/source remove -1001234567890`\n"
            "`/source list`",
            parse_mode="Markdown",
        )
        return

    action = args[0].lower()

    # /source list
    if action == "list":
        sources = get_sources()

        await update.message.reply_text(
            _format_sources(sources),
            parse_mode="Markdown",
        )
        return

    # /source add
    if action == "add":
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Chat ID is missing.\n\n"
                "Example:\n"
                "`/source add -1001234567890 My Channel`",
                parse_mode="Markdown",
            )
            return

        try:
            chat_id = int(args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid chat ID."
            )
            return

        title = " ".join(args[2:]).strip()

        if not title:
            title = str(chat_id)

        try:
            chat = await context.bot.get_chat(chat_id)

            real_title = (
                getattr(chat, "title", None)
                or getattr(chat, "username", None)
                or title
            )

            chat_type = getattr(chat, "type", "") or ""

        except Exception:
            real_title = title
            chat_type = ""

        add_source(
            chat_id=chat_id,
            title=real_title,
            chat_type=chat_type,
        )

        await update.message.reply_text(
            "✅ Source added successfully.\n\n"
            f"📌 Title: {real_title}\n"
            f"🆔 ID: `{chat_id}`",
            parse_mode="Markdown",
        )
        return

    # /source remove
    if action == "remove":
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Chat ID is missing.\n\n"
                "Example:\n"
                "`/source remove -1001234567890`",
                parse_mode="Markdown",
            )
            return

        try:
            chat_id = int(args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid chat ID."
            )
            return

        sources = get_sources()

        if str(chat_id) not in sources:
            await update.message.reply_text(
                "⚠️ This source is not in the approved source list."
            )
            return

        remove_source(chat_id)

        await update.message.reply_text(
            "🗑️ Source removed successfully.\n\n"
            f"🆔 ID: `{chat_id}`",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        "❌ Unknown source action.\n\n"
        "Available commands:\n"
        "`/source add <chat_id> <title>`\n"
        "`/source remove <chat_id>`\n"
        "`/source list`",
        parse_mode="Markdown",
    )
