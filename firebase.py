import json
import os
import threading
from datetime import datetime, timezone
from firebase_admin import credentials, db, initialize_app, get_app
from config import FIREBASE_DATABASE_URL, FIREBASE_CREDENTIALS_JSON, FIREBASE_CREDENTIALS_FILE

_lock = threading.Lock()
_initialized = False

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

def ensure_user(user):
    r = ref(f"users/{user.id}")
    current = r.get() or {}
    if not current:
        r.set({
            "user_id": user.id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "language": "hi",
            "consent": "pending",
            "position": 0,
            "joined_at": now_iso(),
            "last_activity": now_iso(),
            "videos_requested": 0,
            "videos_sent": 0,
            "failed_sends": 0,
        })
    else:
        r.update({
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_activity": now_iso(),
        })
    return r.get() or {}

def get_user(user_id):
    return ref(f"users/{user_id}").get() or {}

def update_user(user_id, data):
    data = dict(data)
    data["last_activity"] = now_iso()
    ref(f"users/{user_id}").update(data)

def get_sources():
    data = ref("sources").get() or {}
    return data

def add_source(chat_id, title="", chat_type=""):
    ref(f"sources/{chat_id}").set({
        "chat_id": chat_id,
        "title": title,
        "type": chat_type,
        "enabled": True,
        "added_at": now_iso(),
    })

def remove_source(chat_id):
    ref(f"sources/{chat_id}").delete()

def set_position(user_id, position):
    update_user(user_id, {"position": int(position)})

def get_pending_deletions():
    return ref("cleanup").get() or {}

def add_cleanup(user_id, chat_id, message_id, delete_at):
    ref(f"cleanup/{user_id}/{message_id}").set({
        "chat_id": chat_id,
        "message_id": message_id,
        "delete_at": delete_at,
    })

def remove_cleanup(user_id, message_id):
    ref(f"cleanup/{user_id}/{message_id}").delete()

def stats():
    users = ref("users").get() or {}
    sources = ref("sources").get() or {}
    total_requests = sum(int(v.get("videos_requested", 0)) for v in users.values() if isinstance(v, dict))
    total_sent = sum(int(v.get("videos_sent", 0)) for v in users.values() if isinstance(v, dict))
    failed = sum(int(v.get("failed_sends", 0)) for v in users.values() if isinstance(v, dict))
    return {
        "users": len(users),
        "sources": len(sources),
        "requests": total_requests,
        "videos_sent": total_sent,
        "failed": failed,
    }
