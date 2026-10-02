import json
import os
import threading
from datetime import datetime, timezone, timedelta
from firebase_admin import credentials, db, initialize_app, get_app
from config import FIREBASE_DATABASE_URL, FIREBASE_CREDENTIALS_JSON, FIREBASE_CREDENTIALS_FILE, ACTIVE_USER_DAYS

_lock = threading.Lock()
_initialized = False

LANGUAGE_ALIASES = {"en","hi","bho","bn","te","mr","ta","gu","ur","kn","ml","pa","as","mai","sa","ne","kok","sd","doi","ks","mni","brx","sat","or","ru","zh","ja","es","fr","de","pt","ar","tr","id","vi","ko","it","nl","pl","uk","fa","th"}

def detect_language(user):
    raw = (getattr(user, "language_code", "") or "").lower().split("-")[0].split("_")[0]
    return raw if raw in LANGUAGE_ALIASES else "hi"

def init_firebase():
    global _initialized
    if _initialized:
        return
    if not FIREBASE_DATABASE_URL:
        raise RuntimeError("FIREBASE_DATABASE_URL is missing")
    if FIREBASE_CREDENTIALS_JSON:
        info = json.loads(FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(info)
    elif FIREBASE_CREDENTIALS_FILE:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_FILE)
    else:
        raise RuntimeError("Firebase credentials are missing")
    try:
        get_app()
    except ValueError:
        initialize_app(cred, {"databaseURL": FIREBASE_DATABASE_URL})
    _initialized = True

def ref(path):
    init_firebase()
    return db.reference(path)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def _full_name(user):
    return " ".join(x for x in [getattr(user, "first_name", ""), getattr(user, "last_name", "")] if x).strip()

def ensure_user(user):
    r = ref(f"users/{user.id}")
    now = now_iso()
    current = r.get() or {}
    base = {
        "user_id": user.id,
        "username": getattr(user, "username", "") or "",
        "first_name": getattr(user, "first_name", "") or "",
        "last_name": getattr(user, "last_name", "") or "",
        "full_name": _full_name(user),
        "language": current.get("language") or detect_language(user),
        "consent": current.get("consent", "pending"),
        "position": int(current.get("position", 0) or 0),
        "joined_at": current.get("joined_at", now),
        "last_activity": now,
        "last_request_at": current.get("last_request_at", ""),
        "last_video_sent_at": current.get("last_video_sent_at", ""),
        "cooldown_until": current.get("cooldown_until", ""),
        "videos_requested": int(current.get("videos_requested", 0) or 0),
        "successful_requests": int(current.get("successful_requests", 0) or 0),
        "failed_requests": int(current.get("failed_requests", 0) or 0),
        "videos_sent": int(current.get("videos_sent", 0) or 0),
        "videos_failed": int(current.get("videos_failed", 0) or 0),
        "total_batches": int(current.get("total_batches", 0) or 0),
    }
    r.set(base) if not current else r.update({
        "username": base["username"], "first_name": base["first_name"],
        "last_name": base["last_name"], "full_name": base["full_name"],
        "last_activity": now,
    })
    return r.get() or base

def get_user(user_id):
    return ref(f"users/{user_id}").get() or {}

def update_user(user_id, data):
    data = dict(data)
    data["last_activity"] = now_iso()
    ref(f"users/{user_id}").update(data)

def log_activity(user_id, event, details=None):
    payload = {"time": now_iso(), "event": event, "details": details or {}}
    try:
        ref(f"activity/{user_id}").push(payload)
    except Exception as e:
        print("[firebase] activity log warning:", e)

def get_activity(user_id, limit=20):
    data = ref(f"activity/{user_id}").get() or {}
    if not isinstance(data, dict):
        return []
    items = list(data.values())
    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return items[:max(1, int(limit))]

def get_all_users():
    data = ref("users").get() or {}
    return data if isinstance(data, dict) else {}

def get_sources():
    data = ref("sources").get() or {}
    return data if isinstance(data, dict) else {}

def add_source(chat_id, title="", chat_type=""):
    ref(f"sources/{chat_id}").set({
        "chat_id": int(chat_id), "title": title, "type": chat_type,
        "enabled": True, "added_at": now_iso(),
    })

def remove_source(chat_id):
    ref(f"sources/{chat_id}").delete()

def set_position(user_id, position):
    update_user(user_id, {"position": int(position)})

def get_pending_deletions():
    return ref("cleanup").get() or {}

def add_cleanup(user_id, chat_id, message_id, delete_at):
    ref(f"cleanup/{user_id}/{message_id}").set({
        "chat_id": int(chat_id), "message_id": int(message_id), "delete_at": delete_at,
    })

def remove_cleanup(user_id, message_id):
    ref(f"cleanup/{user_id}/{message_id}").delete()

def record_broadcast(total, success, failed, kind="broadcast"):
    r = ref("broadcasts").push({
        "time": now_iso(), "type": kind, "total": int(total),
        "success": int(success), "failed": int(failed),
    })
    ref("stats/broadcasts_total").transaction(lambda x: int(x or 0) + 1)
    ref("stats/broadcasts_sent").transaction(lambda x: int(x or 0) + int(success))
    ref("stats/broadcasts_failed").transaction(lambda x: int(x or 0) + int(failed))
    return r.key


def get_bot_enabled():
    value = ref("settings/video_parsing_enabled").get()
    if value is None:
        ref("settings/video_parsing_enabled").set(True)
        return True
    return bool(value)

def set_bot_enabled(enabled):
    ref("settings/video_parsing_enabled").set(bool(enabled))
    return bool(enabled)

def stats():
    users = get_all_users()
    sources = get_sources()
    now = datetime.now(timezone.utc)
    active_cutoff = now - timedelta(days=ACTIVE_USER_DAYS)
    active = 0
    requests = sent = failed = batches = requested_videos = 0
    for v in users.values():
        if not isinstance(v, dict):
            continue
        try:
            last = datetime.fromisoformat(str(v.get("last_activity", "")).replace("Z", "+00:00"))
            if last >= active_cutoff:
                active += 1
        except Exception:
            pass
        requests += int(v.get("videos_requested", 0) or 0)
        sent += int(v.get("videos_sent", 0) or 0)
        failed += int(v.get("failed_requests", 0) or 0)
        batches += int(v.get("total_batches", 0) or 0)
        requested_videos += int(v.get("videos_requested", 0) or 0) * 1
    b = ref("stats").get() or {}
    enabled_sources = sum(1 for x in sources.values() if isinstance(x, dict) and x.get("enabled"))
    return {
        "users": len(users), "active_users": active,
        "sources": len(sources), "enabled_sources": enabled_sources,
        "requests": requests, "batches": batches,
        "videos_sent": sent, "failed": failed,
        "broadcasts": int(b.get("broadcasts_total", 0) or 0),
        "broadcast_sent": int(b.get("broadcasts_sent", 0) or 0),
        "broadcast_failed": int(b.get("broadcasts_failed", 0) or 0),
    }
