import json
from pathlib import Path
from firebase import get_user

BASE = Path(__file__).resolve().parent.parent / "locales"
_cache = {}

def language(uid):
    return (get_user(uid).get("language") or "hi").lower()

def t(uid, key, **kwargs):
    lang = language(uid)
    if lang not in _cache:
        p = BASE / f"{lang}.json"
        if not p.exists(): p = BASE / "hi.json"
        _cache[lang] = json.loads(p.read_text(encoding="utf-8"))
    value = _cache[lang].get(key)
    if value is None:
        value = _cache["en"].get(key, key) if "en" in _cache else key
    try:
        return value.format(**kwargs)
    except Exception:
        return value
