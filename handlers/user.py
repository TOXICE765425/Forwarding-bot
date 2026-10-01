import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes
from firebase import ensure_user, get_user, update_user, set_position, get_pending_deletions, add_cleanup, remove_cleanup, log_activity
from config import VIDEOS_PER_REQUEST, AUTO_DELETE_HOURS, VIDEO_COOLDOWN_MINUTES
from utils.i18n import t, language


def _parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _remaining(value):
    dt = _parse_dt(value)
    if not dt:
        return 0
    return max(0, int((dt - datetime.now(timezone.utc)).total_seconds()))


async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    uid = update.effective_user.id
    ensure_user(update.effective_user)
    text = (
        f"<b>{t(uid, 'help_title')}</b>\n\n"
        f"{t(uid, 'help', count=VIDEOS_PER_REQUEST, cooldown=VIDEO_COOLDOWN_MINUTES, hours=AUTO_DELETE_HOURS)}"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML")


async def video_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    user = update.effective_user
    uid = user.id
    data = ensure_user(user)
    text = (update.message.text or "").strip()
    # Accept the currently selected language's label, plus labels from all locale files.
    video_labels = {t(uid, "video_button")}
    for code in ["en", "hi", "bn", "te", "mr", "ta", "gu", "ur", "kn", "ml", "pa", "ru", "zh", "ja", "es", "fr", "de", "pt", "ar", "tr", "id", "vi", "ko", "it", "nl", "pl", "uk", "fa", "th"]:
        try:
            import json
            from pathlib import Path
            p = Path(__file__).resolve().parent.parent / "locales" / f"{code}.json"
            if p.exists():
                video_labels.add(json.loads(p.read_text(encoding="utf8")).get("video_button", ""))
        except Exception:
            pass
    if text not in video_labels:
        # Help labels are handled here so the single text handler remains simple.
        help_labels = {t(uid, "help_button")}
        if text in help_labels:
            await help_button(update, context)
        return

    if data.get("consent") != "agree":
        await update.message.reply_text(t(uid, "select_agree"))
        return

    remaining = _remaining(data.get("cooldown_until", ""))
    if remaining > 0:
        minutes, seconds = divmod(remaining, 60)
        await update.message.reply_text(t(uid, "cooldown", minutes=minutes, seconds=seconds), parse_mode="HTML")
        log_activity(uid, "cooldown_click", {"remaining_seconds": remaining})
        return

    client = context.application.bot_data["source_client"]
    position = max(0, int(data.get("position", 0) or 0))
    now = datetime.now(timezone.utc)
    update_user(uid, {"videos_requested": int(data.get("videos_requested", 0) or 0) + 1, "last_request_at": now.isoformat()})
    log_activity(uid, "video_request", {"position": position, "batch_size": VIDEOS_PER_REQUEST})
    status = await update.message.reply_text(t(uid, "searching"), parse_mode="HTML")

    try:
        messages, total = await client.get_video_messages(position, VIDEOS_PER_REQUEST)
    except Exception as e:
        latest = get_user(uid)
        update_user(uid, {"failed_requests": int(latest.get("failed_requests", 0) or 0) + 1})
        log_activity(uid, "request_failed", {"error": type(e).__name__})
        await status.edit_text(t(uid, "scan_failed", error=type(e).__name__), parse_mode="HTML")
        return

    if not messages and total > 0:
        position = 0
        messages, total = await client.get_video_messages(0, VIDEOS_PER_REQUEST)
        if messages:
            set_position(uid, 0)

    if not messages:
        latest = get_user(uid)
        update_user(uid, {"failed_requests": int(latest.get("failed_requests", 0) or 0) + 1})
        log_activity(uid, "no_videos", {"total": total})
        await status.edit_text(t(uid, "none"), parse_mode="HTML")
        return

    try:
        sent = await client.copy_messages_via_bot(context.bot, uid, messages)
    except Exception as e:
        latest = get_user(uid)
        update_user(uid, {"failed_requests": int(latest.get("failed_requests", 0) or 0) + 1, "videos_failed": int(latest.get("videos_failed", 0) or 0) + len(messages)})
        log_activity(uid, "copy_failed", {"error": type(e).__name__, "attempted": len(messages)})
        await status.edit_text(t(uid, "failed", error=type(e).__name__), parse_mode="HTML")
        return

    if not sent:
        latest = get_user(uid)
        update_user(uid, {"failed_requests": int(latest.get("failed_requests", 0) or 0) + 1, "videos_failed": int(latest.get("videos_failed", 0) or 0) + len(messages)})
        log_activity(uid, "copy_failed", {"attempted": len(messages), "sent": 0})
        await status.edit_text(t(uid, "failed_simple"), parse_mode="HTML")
        return

    new_position = position + len(sent)
    if new_position >= total:
        new_position = 0
    set_position(uid, new_position)
    latest = get_user(uid)
    cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=VIDEO_COOLDOWN_MINUTES)
    update_user(uid, {
        "videos_sent": int(latest.get("videos_sent", 0) or 0) + len(sent),
        "videos_failed": int(latest.get("videos_failed", 0) or 0) + max(0, len(messages) - len(sent)),
        "successful_requests": int(latest.get("successful_requests", 0) or 0) + 1,
        "total_batches": int(latest.get("total_batches", 0) or 0) + 1,
        "last_video_sent_at": datetime.now(timezone.utc).isoformat(),
        "cooldown_until": cooldown_until.isoformat(),
    })
    log_activity(uid, "video_batch_sent", {"sent": len(sent), "attempted": len(messages), "total_available": total, "next_position": new_position, "cooldown_until": cooldown_until.isoformat()})
    delete_at = datetime.now(timezone.utc) + timedelta(hours=AUTO_DELETE_HOURS)
    for copied in sent:
        mid = getattr(copied, "message_id", None)
        if mid:
            add_cleanup(uid, uid, mid, delete_at.isoformat())

    await status.edit_text(t(uid, "sent_status", count=len(sent), cooldown=VIDEO_COOLDOWN_MINUTES, hours=AUTO_DELETE_HOURS), parse_mode="HTML")


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
                        remove_cleanup(uid, mid)
        except Exception as e:
            print("cleanup:", e)
        await asyncio.sleep(60)
