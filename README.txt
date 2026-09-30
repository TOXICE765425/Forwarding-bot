FORWARDING-BOT: NO-DOWNLOAD COPY UPDATE

1) Replace the current telegram_client.py with the included telegram_client.py.
2) Replace handlers/user.py with the included handlers/user.py ONLY if your current file has the same firebase functions used here.
3) In config.py make sure:
   VIDEOS_PER_REQUEST=5
4) The Telegram BOT must be admin/member with permission to access/copy messages from every source channel configured in Firebase.
5) This implementation uses Bot API copyMessage. The media file is NOT downloaded to Render.
6) copyMessage removes the normal forwarded-from channel header. protect_content=True asks Telegram to restrict forwarding/saving.
7) If you use AUTO_DELETE_HOURS, the copied bot messages are still deleted by the existing cleanup worker.

IMPORTANT:
- Do not expose your BOT_TOKEN or SESSION_BASE64 in logs/GitHub.
- If a bot token was pasted publicly, revoke it with BotFather and update Render.
- Telegram protection cannot prevent screenshots/screen recording/external capture.
