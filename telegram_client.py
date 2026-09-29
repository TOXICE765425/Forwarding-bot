import os
import base64
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import DocumentAttributeVideo

from config import API_ID, API_HASH, SESSION_NAME, SESSION_BASE64, PHONE_NUMBER
from firebase import get_sources

MAX_BOT_UPLOAD = 49 * 1024 * 1024
SEND_TIMEOUT = 300


def restore_session_from_base64():
    if not SESSION_BASE64:
        return

    session_path = Path(SESSION_NAME + ".session")
    session_path.parent.mkdir(parents=True, exist_ok=True)

    if session_path.exists() and os.getenv("FORCE_SESSION_RESTORE", "").lower() not in {
        "1", "true", "yes"
    }:
        print(f"[session] existing session found: {session_path}")
        return

    try:
        raw = base64.b64decode(SESSION_BASE64.strip(), validate=True)
        if not raw.startswith(b"SQLite format 3"):
            print("[session] warning: SESSION_BASE64 does not look like a SQLite session")
        session_path.write_bytes(raw)
        try:
            os.chmod(session_path, 0o600)
        except OSError:
            pass
        print(f"[session] restored: {session_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to restore SESSION_BASE64: {e}") from e


class TelegramSourceClient:
    def __init__(self):
        if not API_ID or not API_HASH:
            raise RuntimeError("API_ID/API_HASH are required")

        restore_session_from_base64()
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self._entity_cache = {}

    async def start(self):
        await self.client.connect()

        if await self.client.is_user_authorized():
            try:
                me = await self.client.get_me()
                name = " ".join(
                    x for x in [getattr(me, "first_name", None),
                                getattr(me, "last_name", None)] if x
                ).strip()
                username = f"@{me.username}" if getattr(me, "username", None) else "no username"
                print(f"[telegram] authorized account: {name or 'Unknown'} | {username} | id={me.id}")
            except Exception as e:
                print(f"[telegram] account info warning: {e}")
            print("[telegram] existing session authorized")
            return

        if not PHONE_NUMBER:
            raise RuntimeError("MTProto session is not authorized. Set SESSION_BASE64.")

        await self.client.send_code_request(PHONE_NUMBER)
        code = input("Enter Telegram login code: ").strip()

        try:
            await self.client.sign_in(PHONE_NUMBER, code)
        except SessionPasswordNeededError:
            password = input("Enter Telegram 2FA password: ")
            await self.client.sign_in(password=password)

    async def stop(self):
        if self.client.is_connected():
            await self.client.disconnect()

    async def _sources(self):
        result = []
        for key, data in (get_sources() or {}).items():
            if not isinstance(data, dict) or not data.get("enabled"):
                continue
            try:
                result.append(int(data["chat_id"]))
            except Exception as e:
                print(f"[source] invalid chat_id for {key}: {e}")

        result = list(dict.fromkeys(result))
        print(f"[source] enabled sources: {len(result)} -> {result}")
        return result

    async def _resolve_source(self, chat_id):
        chat_id = int(chat_id)
        if chat_id in self._entity_cache:
            return self._entity_cache[chat_id]

        entity = await self.client.get_entity(chat_id)
        self._entity_cache[chat_id] = entity
        title = getattr(entity, "title", None) or getattr(entity, "username", None) or str(chat_id)
        print(f"[source] resolved {chat_id} -> {title} (type={type(entity).__name__})")
        return entity

    @staticmethod
    def _is_video_message(msg):
        if not msg:
            return False
        if getattr(msg, "video", None):
            return True

        document = getattr(msg, "document", None)
        if not document:
            return False

        mime = (getattr(document, "mime_type", None) or "").lower().strip()
        if mime.startswith("video/"):
            return True

        for attr in getattr(document, "attributes", None) or []:
            if isinstance(attr, DocumentAttributeVideo):
                return True

        filename = None
        try:
            filename = getattr(msg.file, "name", None)
        except Exception:
            pass

        if not filename:
            for attr in getattr(document, "attributes", None) or []:
                filename = getattr(attr, "file_name", None)
                if filename:
                    break

        return bool(
            filename and Path(filename).suffix.lower() in {
                ".mp4", ".mkv", ".mov", ".avi", ".webm",
                ".m4v", ".3gp", ".mpeg", ".mpg", ".wmv",
                ".flv", ".ts"
            }
        )

    async def get_video_messages(self, start_position, limit):
        try:
            start_position = max(0, int(start_position))
        except Exception:
            start_position = 0

        try:
            limit = max(1, int(limit))
        except Exception:
            limit = 5

        found = []
        seen = set()
        sources = await self._sources()

        for chat_id in sources:
            try:
                entity = await self._resolve_source(chat_id)
                title = getattr(entity, "title", None) or getattr(entity, "username", None) or str(chat_id)
                scanned = 0
                count = 0

                print(f"[source] scanning {title} ({chat_id})...")

                async for msg in self.client.iter_messages(entity, limit=None, reverse=True):
                    scanned += 1
                    if not self._is_video_message(msg):
                        continue

                    key = (chat_id, getattr(msg, "id", None))
                    if key in seen:
                        continue

                    seen.add(key)
                    found.append(msg)
                    count += 1

                print(f"[source] {title} ({chat_id}): scanned={scanned}, videos={count}")

            except Exception as e:
                print(f"[source] failed {chat_id}: {type(e).__name__}: {e}")

        found.sort(
            key=lambda m: getattr(m, "date", None)
            or datetime.min.replace(tzinfo=timezone.utc)
        )

        total = len(found)
        selected = found[start_position:start_position + limit]

        print(
            f"[source] total videos={total}, position={start_position}, "
            f"requested={limit}, returning={len(selected)}"
        )
        return selected, total

    @staticmethod
    def _filename(msg, index):
        try:
            name = getattr(msg.file, "name", None)
        except Exception:
            name = None
        return Path(name).name if name else f"video_{index}.mp4"

    @staticmethod
    def _caption(msg):
        text = (getattr(msg, "text", None) or "").strip()
        return text[:1000] + ("..." if len(text) > 1000 else "")

    async def send_videos_via_bot(self, bot, user_id, messages):
        """
        Telethon reads/downloads the source media.
        The Telegram Bot API sends the actual message to the user.
        """
        sent = []

        with tempfile.TemporaryDirectory(prefix="forwarding_bot_") as temp_dir:
            for index, msg in enumerate(messages, start=1):
                message_id = getattr(msg, "id", None)
                path = None

                try:
                    target = Path(temp_dir) / self._filename(msg, index)
                    print(f"[media] downloading message {message_id} -> {target.name}")

                    result = await self.client.download_media(msg, file=str(target))
                    if not result:
                        print(f"[media] download failed for {message_id}")
                        continue

                    path = Path(result)
                    size = path.stat().st_size
                    print(f"[media] downloaded {message_id}: {size / 1024 / 1024:.2f} MB")

                    if size > MAX_BOT_UPLOAD:
                        print(f"[media] skipped {message_id}: larger than 49 MB")
                        continue

                    caption = self._caption(msg)

                    try:
                        with path.open("rb") as f:
                            out = await bot.send_video(
                                chat_id=user_id,
                                video=f,
                                caption=caption or None,
                                filename=path.name,
                                supports_streaming=True,
                                read_timeout=SEND_TIMEOUT,
                                write_timeout=SEND_TIMEOUT,
                                connect_timeout=60,
                                pool_timeout=60,
                            )
                    except Exception as video_error:
                        print(
                            f"[media] send_video failed for {message_id}: "
                            f"{type(video_error).__name__}: {video_error}"
                        )
                        with path.open("rb") as f:
                            out = await bot.send_document(
                                chat_id=user_id,
                                document=f,
                                caption=caption or None,
                                filename=path.name,
                                read_timeout=SEND_TIMEOUT,
                                write_timeout=SEND_TIMEOUT,
                                connect_timeout=60,
                                pool_timeout=60,
                            )

                    sent.append(out)
                    print(
                        f"[media] BOT SENT source={message_id} "
                        f"destination_message={out.id}"
                    )

                except Exception as e:
                    print(f"[media] FAILED source={message_id}: {type(e).__name__}: {e}")

                finally:
                    if path:
                        try:
                            path.unlink(missing_ok=True)
                        except Exception:
                            pass

        print(f"[media] bot delivery complete: {len(sent)}/{len(messages)}")
        return sent
