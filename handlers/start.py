from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes
from firebase import ensure_user, get_user, update_user
from config import DEFAULT_LANGUAGE, CONSENT_AFTER_AGREE, WELCOME_USE_PROFILE_PHOTO
from utils.i18n import t, detect_language, supported_languages, language_name

# Keep all currently supported Indian languages and add widely used world languages.
LANGUAGES = {
    "hi": "🇮🇳 हिन्दी", "bho": "🇮🇳 भोजपुरी", "en": "🇬🇧 English", "bn": "🇮🇳 বাংলা", "te": "🇮🇳 తెలుగు",
    "mr": "🇮🇳 मराठी", "ta": "🇮🇳 தமிழ்", "gu": "🇮🇳 ગુજરાતી", "ur": "🇮🇳 اردو",
    "kn": "🇮🇳 ಕನ್ನಡ", "ml": "🇮🇳 മലയാളം", "pa": "🇮🇳 ਪੰਜਾਬੀ", "as": "🇮🇳 অসমীয়া",
    "mai": "🇮🇳 मैथिली", "sa": "🇮🇳 संस्कृत", "ne": "🇳🇵 नेपाली", "kok": "🇮🇳 कोंकणी",
    "sd": "🇮🇳 سنڌي", "doi": "🇮🇳 डोगरी", "ks": "🇮🇳 कश्मीरी", "mni": "🇮🇳 মণিপুরি",
    "brx": "🇮🇳 बोडो", "sat": "🇮🇳 संताली", "or": "🇮🇳 ଓଡ଼ିଆ", "ru": "🇷🇺 Русский",
    "zh": "🇨🇳 中文", "ja": "🇯🇵 日本語", "es": "🇪🇸 Español", "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch", "pt": "🇵🇹 Português", "ar": "🌍 العربية", "tr": "🇹🇷 Türkçe",
    "id": "🇮🇩 Bahasa Indonesia", "vi": "🇻🇳 Tiếng Việt", "ko": "🇰🇷 한국어", "it": "🇮🇹 Italiano",
    "nl": "🇳🇱 Nederlands", "pl": "🇵🇱 Polski", "uk": "🇺🇦 Українська", "fa": "🇮🇷 فارسی",
    "th": "🇹🇭 ไทย",
}


def language_keyboard():
    items = list(LANGUAGES.items())
    rows = []
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(items[i][1], callback_data=f"lang:{items[i][0]}")]
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(items[i + 1][1], callback_data=f"lang:{items[i + 1][0]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("↩️ Back", callback_data="lang:back")])
    return InlineKeyboardMarkup(rows)


def consent_keyboard(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, "disagree"), callback_data="disagree"),
         InlineKeyboardButton(t(uid, "agree"), callback_data="agree")],
        [InlineKeyboardButton(t(uid, "language"), callback_data="lang:menu")],
    ])


def welcome_keyboard(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, "language"), callback_data="lang:menu")]
    ])


def menu_keyboard(uid):
    return ReplyKeyboardMarkup(
        [[t(uid, "video_button")]],
        resize_keyboard=True,
        is_persistent=True,
    )


def terms(uid):
    return f"<b>{t(uid, 'terms_title')}</b>\n\n{t(uid, 'terms')}\n\n{t(uid, 'agree_note')}"


def welcome_text(uid, name):
    return f"<b>{t(uid, 'welcome', name=name)}</b>\n\n{t(uid, 'activated')}"


async def _send_welcome(context, user, uid, old_message=None):
    caption = welcome_text(uid, user.first_name or "User")
    kb = welcome_keyboard(uid)
    if WELCOME_USE_PROFILE_PHOTO:
        try:
            photos = await context.bot.get_user_profile_photos(user.id, limit=1)
            if photos.total_count:
                if old_message:
                    try:
                        await old_message.delete()
                    except Exception:
                        pass
                return await context.bot.send_photo(
                    chat_id=user.id,
                    photo=photos.photos[0][-1].file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
        except Exception:
            pass

    if old_message:
        try:
            await old_message.edit_text(caption, parse_mode="HTML", reply_markup=kb)
            return old_message
        except Exception:
            pass
    return await context.bot.send_message(chat_id=user.id, text=caption, parse_mode="HTML", reply_markup=kb)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = ensure_user(user)
    uid = user.id
    # Every /start requires a fresh consent. Video access remains blocked until Agree is pressed.
    update_user(uid, {"consent": "pending"})
    await update.message.reply_text(terms(uid), parse_mode="HTML", reply_markup=consent_keyboard(uid))


async def consent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = q.from_user
    uid = user.id

    if q.data == "disagree":
        update_user(uid, {"consent": "disagree"})
        # Show the rejection as a Telegram dialog/alert, not a new chat message.
        await q.answer(t(uid, "not_for_you"), show_alert=True)
        return

    await q.answer()
    update_user(uid, {"consent": "agree"})
    if CONSENT_AFTER_AGREE == "edit":
        await _send_welcome(context, user, uid, old_message=q.message)
    else:
        await _send_welcome(context, user, uid, old_message=q.message)
    # The old consent message is deleted when a profile photo is used; otherwise edited.
    try:
        await context.bot.send_message(chat_id=uid, text=t(uid, "menu_ready"), reply_markup=menu_keyboard(uid))
    except Exception:
        pass


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = q.from_user
    uid = user.id

    if q.data == "lang:menu":
        await q.answer()
        try:
            if q.message.photo:
                await q.message.edit_caption(t(uid, "select_language"), parse_mode="HTML", reply_markup=language_keyboard())
            else:
                await q.message.edit_text(t(uid, "select_language"), parse_mode="HTML", reply_markup=language_keyboard())
        except Exception:
            pass
        return

    if q.data == "lang:back":
        await q.answer()
        data = get_user(uid)
        update_user(uid, {"language": data.get("language") or DEFAULT_LANGUAGE})
        try:
            if q.message.photo:
                await q.message.edit_caption(welcome_text(uid, user.first_name or "User"), parse_mode="HTML", reply_markup=welcome_keyboard(uid))
            else:
                await q.message.edit_text(welcome_text(uid, user.first_name or "User"), parse_mode="HTML", reply_markup=welcome_keyboard(uid))
        except Exception:
            pass
        return

    lang = q.data.split(":", 1)[1]
    if lang not in LANGUAGES:
        await q.answer("Language unavailable", show_alert=True)
        return

    update_user(uid, {"language": lang})
    await q.answer(f"✅ {LANGUAGES[lang]}")
    try:
        if q.message.photo:
            await q.message.edit_caption(welcome_text(uid, user.first_name or "User"), parse_mode="HTML", reply_markup=welcome_keyboard(uid))
        else:
            await q.message.edit_text(welcome_text(uid, user.first_name or "User"), parse_mode="HTML", reply_markup=welcome_keyboard(uid))
    except Exception:
        pass
    await context.bot.send_message(chat_id=uid, text=t(uid, "menu_ready"), reply_markup=menu_keyboard(uid))
