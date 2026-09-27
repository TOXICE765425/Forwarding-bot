from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes
from firebase import ensure_user, update_user
from config import DEFAULT_LANGUAGE

LANGUAGES = {
    "hi": "🇮🇳 हिन्दी",
    "en": "🇬🇧 English",
    "bn": "🇮🇳 বাংলা",
    "te": "🇮🇳 తెలుగు",
    "mr": "🇮🇳 मराठी",
    "ta": "🇮🇳 தமிழ்",
    "gu": "🇮🇳 ગુજરાતી",
    "ur": "🇮🇳 اردو / 🇵🇰 اردو",
    "kn": "🇮🇳 ಕನ್ನಡ",
    "ml": "🇮🇳 മലയാളം",
    "pa": "🇮🇳 ਪੰਜਾਬੀ",
    "as": "🇮🇳 অসমীয়া",
    "mai": "🇮🇳 मैथिली",
    "sa": "🇮🇳 संस्कृत",
    "ne": "🇮🇳 नेपाली",
    "kok": "🇮🇳 कोंकणी",
    "sd": "🇮🇳 سنڌي",
    "doi": "🇮🇳 डोगरी",
    "ks": "🇮🇳 कश्मीरी",
    "mni": "🇮🇳 মণিপুরি",
    "brx": "🇮🇳 बोडो",
    "sat": "🇮🇳 संताली",
    "or": "🇮🇳 ଓଡ଼ିଆ",
    "ru": "🇷🇺 Русский",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
}

def language_keyboard():
    items = list(LANGUAGES.items())
    rows = []
    for i in range(0, len(items), 2):
        rows.append([
            InlineKeyboardButton(items[i][1], callback_data=f"lang:{items[i][0]}"),
            *([InlineKeyboardButton(items[i+1][1], callback_data=f"lang:{items[i+1][0]}")] if i+1 < len(items) else [])
        ])
    return InlineKeyboardMarkup(rows)

def consent_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ Disagree", callback_data="disagree"),
            InlineKeyboardButton("✅ Agree", callback_data="agree"),
        ],
        [InlineKeyboardButton("🌐 Language", callback_data="lang:menu")],
    ])

TERMS = (
    "📜 <b>Before You Continue</b>\n\n"
    "This bot provides authorized video access from configured Telegram sources. "
    "Please use it only where you have permission to access and receive the content.\n\n"
    "By pressing <b>Agree</b>, you confirm that you accept these terms and want to continue.\n\n"
    "Choose your language with the Language button."
)

def menu_keyboard():
    return ReplyKeyboardMarkup(
        [["🎬 Video File"], ["ℹ️ Help"]],
        resize_keyboard=True,
        is_persistent=True,
    )

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)
    await update.message.reply_text(TERMS, parse_mode="HTML", reply_markup=consent_keyboard())

async def consent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user

    if q.data == "disagree":
        update_user(user.id, {"consent": "disagree"})
        await q.edit_message_text(
            "❌ <b>This Is Not For You</b>\n\n"
            "Aap is bot ko use karne ke yogye nahi hai.\n"
            "Access has been disabled.",
            parse_mode="HTML",
        )
        return

    update_user(user.id, {"consent": "agree"})
    try:
        photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count:
            await context.bot.send_photo(
                chat_id=user.id,
                photo=photos.photos[0][-1].file_id,
                caption=f"🎉 <b>Welcome, {user.first_name or 'User'}!</b>\n\n"
                        "Aapka access activate ho gaya hai.",
                parse_mode="HTML",
                reply_markup=menu_keyboard(),
            )
            return
    except Exception:
        pass

    await context.bot.send_message(
        chat_id=user.id,
        text=f"🎉 <b>Welcome, {user.first_name or 'User'}!</b>\n\nAapka access activate ho gaya hai.",
        parse_mode="HTML",
        reply_markup=menu_keyboard(),
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user

    if q.data == "lang:menu":
        await q.message.reply_text("🌐 <b>Select your language:</b>", parse_mode="HTML", reply_markup=language_keyboard())
        return

    lang = q.data.split(":", 1)[1]
    update_user(user.id, {"language": lang})
    await q.message.reply_text(
        f"✅ Language selected: {LANGUAGES.get(lang, lang)}\n\n"
        "Ab aap bot ko use kar sakte hain.",
        reply_markup=menu_keyboard(),
    )
