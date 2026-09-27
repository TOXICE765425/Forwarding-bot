# Telegram Video Distribution Bot

Modular Telegram bot for serving authorized videos from approved Telegram channels/groups.

## What it does

- Consent screen: Agree / Disagree / Language
- Multilingual UI scaffold
- Per-user video pagination: 5 videos per request
- Position persists in Firebase
- Approved channel/group sources
- Reads existing Telegram history through MTProto
- Forwards videos directly from Telegram
- Does not download video files to the bot server
- Firebase stores only metadata, counters, source configuration and cleanup metadata
- Sent copies are scheduled for deletion after 2 hours
- Owner statistics and source management
- Docker + Railway + Render + Fly.io deployment files

## Important

The MTProto account used by Telethon must legitimately have access to every source chat.
Use this only for content you are authorized to access and redistribute.

## First run

1. Create a Telegram bot with BotFather and get BOT_TOKEN.
2. Get API_ID and API_HASH from Telegram's official developer portal.
3. Create a Firebase Realtime Database and service account.
4. Put secrets in environment variables.
5. Start locally:
   `pip install -r requirements.txt`
   `python bot.py`
6. On first run, Telethon asks for the login code and 2FA password if enabled.
7. After successful login, the session file is created under `sessions/`.

Never upload the session file or Firebase service-account JSON to GitHub.

## Owner commands

`/admin`
`/source add -1001234567890 Title`
`/source remove -1001234567890`
`/source list`

## Deployment

The same repository can be deployed as a worker/container on Railway, Render, Fly.io, Docker-capable VPS and similar services.

## Data model

Firebase:
- users/
- sources/
- cleanup/

Actual video files are never uploaded to Firebase by this project.


## Multilingual note
The locale system is included for all requested language codes. English is used as a safe fallback for locale keys that have not been professionally translated yet; add reviewed translations to the corresponding JSON files before production use.

## Message deletion
Because the MTProto account forwards the source messages, the MTProto account is also used to delete those forwarded copies after the configured time.
