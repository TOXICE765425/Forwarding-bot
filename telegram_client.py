import os
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH, SESSION_NAME, PHONE_NUMBER, HISTORY_PAGE_SIZE
from firebase import get_sources

class TelegramSourceClient:
    def __init__(self):
        if not API_ID or not API_HASH:
            raise RuntimeError("API_ID/API_HASH are required for MTProto source access")
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            if not PHONE_NUMBER:
                raise RuntimeError(
                    "MTProto session is not authorized. Set PHONE_NUMBER for first login, "
                    "then complete the code/password prompt once."
                )
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
            if isinstance(data, dict) and data.get("enabled"):
                try:
                    result.append(int(data["chat_id"]))
                except Exception:
                    pass
        return result

    async def get_video_messages(self, start_position, limit):
        """
        Reads Telegram history dynamically. No video/file is stored in Firebase.
        Results are sorted by source message date and only exist in memory for this request.
        """
        found = []
        for chat_id in await self._sources():
            try:
                async for msg in self.client.iter_messages(chat_id, limit=None, reverse=True):
                    if not msg or not msg.media:
                        continue
                    # Accept Telegram video documents and native video messages.
                    is_video = bool(getattr(msg, "video", None))
                    if not is_video:
                        doc = getattr(msg, "document", None)
                        mime = getattr(doc, "mime_type", "") if doc else ""
                        is_video = mime.startswith("video/")
                    if is_video:
                        found.append(msg)
            except Exception as e:
                print(f"[source] failed {chat_id}: {e}")

        found.sort(key=lambda m: m.date or datetime.min.replace(tzinfo=timezone.utc))
        return found[start_position:start_position + limit], len(found)

    async def forward_to_user(self, user_id, messages):
        sent = []
        for msg in messages:
            result = await self.client.forward_messages(user_id, msg)
            if isinstance(result, list):
                sent.extend(result)
            else:
                sent.append(result)
        return sent
