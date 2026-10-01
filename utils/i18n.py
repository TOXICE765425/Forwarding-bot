import json
from pathlib import Path
from config import DEFAULT_LANGUAGE

BASE = Path(__file__).resolve().parent.parent / "locales"
_cache = {}

# Telegram language_code -> locale used by this bot.
LANG_ALIASES = {
    "en": "en", "hi": "hi", "bho": "bho", "bn": "bn", "te": "te", "mr": "mr", "ta": "ta", "gu": "gu",
    "ur": "ur", "kn": "kn", "ml": "ml", "pa": "pa", "as": "as", "mai": "mai", "sa": "sa",
    "ne": "ne", "kok": "kok", "sd": "sd", "doi": "doi", "ks": "ks", "mni": "mni", "brx": "brx",
    "sat": "sat", "or": "or", "ru": "ru", "zh": "zh", "ja": "ja", "es": "es", "fr": "fr",
    "de": "de", "pt": "pt", "ar": "ar", "tr": "tr", "id": "id", "vi": "vi", "ko": "ko", "it": "it",
    "nl": "nl", "pl": "pl", "uk": "uk", "fa": "fa", "th": "th",
}


def supported_languages():
    return list(LANG_ALIASES)


def language_name(code):
    return code


def detect_language(user):
    raw = (getattr(user, "language_code", "") or "").lower().split("-")[0].split("_")[0]
    return LANG_ALIASES.get(raw, DEFAULT_LANGUAGE)


def language(uid):
    from firebase import get_user
    value = (get_user(uid).get("language") or DEFAULT_LANGUAGE).lower()
    return value if value in LANG_ALIASES else DEFAULT_LANGUAGE


def t(uid, key, **kwargs):
    lang = language(uid)
    if lang not in _cache:
        p = BASE / f"{lang}.json"
        if not p.exists():
            p = BASE / f"{DEFAULT_LANGUAGE}.json"
        try:
            _cache[lang] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            _cache[lang] = {}
    if "en" not in _cache:
        p = BASE / "en.json"
        _cache["en"] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    value = _cache[lang].get(key) or _cache["en"].get(key) or key
    try:
        return value.format(**kwargs)
    except Exception:
        return value
