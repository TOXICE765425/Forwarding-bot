import os
import base64
from pathlib import Path
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import DocumentAttributeVideo

from config import (
    API_ID,
    API_HASH,
    SESSION_NAME,
    SESSION_BASE64,
    PHONE_NUMBER,
    HISTORY_PAGE_SIZE,
)
from firebase import get_sources


def restore_session_from_base64():
    """
    Restore the Telethon SQLite session from SESSION_BASE64.

    The .session file is created locally on the Render instance.
    It is not stored in GitHub or Firebase.
    """
    if not SESSION_BASE64:
        return

    session_path = Path(SESSION_NAME + ".session")
    session_path.parent.mkdir(parents=True, exist_ok=True)

    # Do not overwrite an already-restored session unless explicitly requested.
    force_restore = os.getenv("FORCE_SESSION_RESTORE", "").lower() in {
        "1",
        "true",
        "yes",
    }

    if session_path.exists() and not force_restore:
        print(f"[session] existing session found: {session_path}")
        return

    try:
        session_bytes = base64.b64decode(
            SESSION_BASE64.strip(),
            validate=True,
        )

        # Basic SQLite-session sanity check.
        if not session_bytes.startswith(b"SQLite format 3"):
            print(
                "[session] warning: SESSION_BASE64 does not look like "
                "a normal SQLite Telethon session."
            )

        session_path.write_bytes(session_bytes)

        try:
            os.chmod(session_path, 0o600)
        except OSError:
            pass

        print(f"[session] restored: {session_path}")

    except Exception as e:
        raise RuntimeError(
            f"Failed to restore SESSION_BASE64: {e}"
        ) from e


class TelegramSourceClient:
    def __init__(self):
        if not API_ID or not API_HASH:
            raise RuntimeError(
                "API_ID/API_HASH are required for MTProto source access"
            )

        restore_session_from_base64()

        self.client = TelegramClient(
            SESSION_NAME,
            API_ID,
            API_HASH,
        )

        # Keep resolved entities in memory so we don't repeatedly resolve
        # the same channel on every request.
        self._entity_cache = {}

    async def start(self):
        await self.client.connect()

        if await self.client.is_user_authorized():
            try:
                me = await self.client.get_me()

                if me:
                    username = (
                        f"@{me.username}"
                        if getattr(me, "username", None)
                        else "no username"
                    )

                    name = " ".join(
                        x
                        for x in [
                            getattr(me, "first_name", None),
                            getattr(me, "last_name", None),
                        ]
                        if x
                    ).strip()

                    print(
                        f"[telegram] authorized account: "
                        f"{name or 'Unknown'} | {username} | id={me.id}"
                    )
            except Exception as e:
                print(f"[telegram] account info warning: {e}")

            print("[telegram] existing session authorized")
            return

        if not PHONE_NUMBER:
            raise RuntimeError(
                "MTProto session is not authorized. "
                "Set SESSION_BASE64 to an authorized Telethon "
                "session or provide PHONE_NUMBER for first login."
            )

        print("[telegram] session is not authorized.")
        print("[telegram] starting interactive first-login flow.")

        await self.client.send_code_request(PHONE_NUMBER)

        code = input(
            "Enter Telegram login code: "
        ).strip()

        try:
            await self.client.sign_in(
                PHONE_NUMBER,
                code,
            )

        except SessionPasswordNeededError:
            password = input(
                "Enter Telegram 2FA password: "
            )

            await self.client.sign_in(
                password=password,
            )

        print("[telegram] login successful")

    async def stop(self):
        if self.client.is_connected():
            await self.client.disconnect()

    async def _sources(self):
        """
        Return enabled source chat IDs from Firebase.
        """
        result = []

        for key, data in (get_sources() or {}).items():
            if not isinstance(data, dict):
                continue

            if not data.get("enabled"):
                continue

            try:
                chat_id = int(data["chat_id"])
                result.append(chat_id)
            except Exception as e:
                print(
                    f"[source] invalid chat_id for {key}: {e}"
                )

        # Remove duplicate source IDs while preserving order.
        result = list(dict.fromkeys(result))

        print(
            f"[source] enabled sources: {len(result)} -> {result}"
        )

        return result

    async def _resolve_source(self, chat_id):
        """
        Resolve a Telegram source to an actual Telethon entity.

        This is more reliable than repeatedly passing a raw -100... ID
        directly to iter_messages().
        """
        chat_id = int(chat_id)

        if chat_id in self._entity_cache:
            return self._entity_cache[chat_id]

        try:
            entity = await self.client.get_entity(chat_id)

            self._entity_cache[chat_id] = entity

            title = (
                getattr(entity, "title", None)
                or getattr(entity, "username", None)
                or str(chat_id)
            )

            print(
                f"[source] resolved {chat_id} -> "
                f"{title} "
                f"(type={type(entity).__name__})"
            )

            return entity

        except Exception as e:
            print(
                f"[source] resolve failed {chat_id}: "
                f"{type(e).__name__}: {e}"
            )
            raise

    @staticmethod
    def _is_video_message(msg):
        """
        Robust Telegram video detection.

        Supports:
        1. Native Telegram video messages.
        2. Videos uploaded as documents.
        3. Documents with Telegram's DocumentAttributeVideo.
        4. Common video file extensions when MIME type is missing.
        """
        if not msg:
            return False

        # Native Telethon convenience property.
        if bool(getattr(msg, "video", None)):
            return True

        document = getattr(msg, "document", None)

        if not document:
            return False

        # MIME type check.
        mime_type = (
            getattr(document, "mime_type", None)
            or ""
        ).lower().strip()

        if mime_type.startswith("video/"):
            return True

        # Telegram document attributes.
        for attribute in (
            getattr(document, "attributes", None) or []
        ):
            if isinstance(attribute, DocumentAttributeVideo):
                return True

        # Fallback: filename extension.
        filename = (
            getattr(msg, "file", None)
            and getattr(msg.file, "name", None)
        )

        if not filename:
            for attribute in (
                getattr(document, "attributes", None) or []
            ):
                name = getattr(attribute, "file_name", None)
                if name:
                    filename = name
                    break

        if filename:
            extension = Path(filename).suffix.lower()

            if extension in {
                ".mp4",
                ".mkv",
                ".mov",
                ".avi",
                ".webm",
                ".m4v",
                ".3gp",
                ".mpeg",
                ".mpg",
                ".wmv",
                ".flv",
                ".ts",
            }:
                return True

        return False

    async def get_video_messages(
        self,
        start_position,
        limit,
    ):
        """
        Read authorized Telegram source history dynamically.

        Videos are NOT stored in Firebase.

        start_position:
            Global position of the user in the combined source list.

        limit:
            Maximum number of videos to return.
        """
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

        if not sources:
            print("[source] no enabled sources found")
            return [], 0

        for chat_id in sources:
            try:
                entity = await self._resolve_source(chat_id)

                source_title = (
                    getattr(entity, "title", None)
                    or getattr(entity, "username", None)
                    or str(chat_id)
                )

                source_video_count = 0
                scanned = 0

                print(
                    f"[source] scanning {source_title} "
                    f"({chat_id})..."
                )

                # HISTORY_PAGE_SIZE is used only as the API page/chunk size.
                # We continue until the complete accessible history is scanned.
                page_size = 100

                try:
                    configured_page_size = int(HISTORY_PAGE_SIZE)
                    if configured_page_size > 0:
                        page_size = min(
                            max(configured_page_size, 20),
                            100,
                        )
                except Exception:
                    pass

                async for msg in self.client.iter_messages(
                    entity,
                    limit=None,
                    reverse=True,
                ):
                    scanned += 1

                    if not self._is_video_message(msg):
                        continue

                    # Message IDs are unique within a Telegram chat.
                    msg_id = getattr(msg, "id", None)

                    unique_key = (
                        chat_id,
                        msg_id,
                    )

                    if unique_key in seen:
                        continue

                    seen.add(unique_key)
                    found.append(msg)
                    source_video_count += 1

                print(
                    f"[source] {source_title} ({chat_id}): "
                    f"scanned={scanned}, "
                    f"videos={source_video_count}"
                )

            except Exception as e:
                print(
                    f"[source] failed {chat_id}: "
                    f"{type(e).__name__}: {e}"
                )

        # Oldest -> newest.
        found.sort(
            key=lambda m: (
                getattr(m, "date", None)
                or datetime.min.replace(tzinfo=timezone.utc)
            )
        )

        total = len(found)

        selected = found[
            start_position:start_position + limit
        ]

        print(
            f"[source] total videos={total}, "
            f"position={start_position}, "
            f"requested={limit}, "
            f"returning={len(selected)}"
        )

        if selected:
            selected_ids = [
                getattr(message, "id", None)
                for message in selected
            ]

            print(
                f"[source] selected message IDs: {selected_ids}"
            )

        return selected, total

    async def forward_to_user(
        self,
        user_id,
        messages,
    ):
        """
        Forward selected messages to the requesting user.

        No video file is downloaded or stored by the bot.
        """
        sent = []

        for msg in messages:
            try:
                result = await self.client.forward_messages(
                    user_id,
                    msg,
                )

                if isinstance(result, list):
                    sent.extend(result)
                else:
                    sent.append(result)

            except Exception as e:
                print(
                    f"[forward] failed "
                    f"user={user_id}, "
                    f"message={getattr(msg, 'id', None)}: "
                    f"{type(e).__name__}: {e}"
                )

        print(
            f"[forward] user={user_id}: "
            f"{len(sent)}/{len(messages)} forwarded"
        )

        return sent
