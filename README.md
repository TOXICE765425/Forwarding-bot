# Forwarding Bot — Complete Firebase + CopyMessage Edition

This bot distributes authorized videos from configured Telegram sources.

## Main features

### User
- `/start` consent + language flow
- `🎬 Video File` sends up to 5 videos per successful request
- 10-minute per-user cooldown after a successful video batch
- Sequence wraps back to the beginning after the last available video
- Firebase permanently stores user profile, counters, position and cooldown
- Sent copies are automatically deleted after `AUTO_DELETE_HOURS`
- Bot API `copyMessage` is used, so Render does not download the video file
- `protect_content=True` is enabled for copied videos

### Owner commands

- `/admin` — owner panel
- `/stats` — complete bot statistics
- `/user` — Firebase user list, `/user 2` for next page
- `/activity USER_ID` — detailed user activity and counters
- `/bots` — compact statistics alias
- `/broadcast` — reply to a message and broadcast it
- `/broadcast bot` — alias for broadcast
- `/broadcast Your text` — text broadcast
- `/source add <chat_id> <title>`
- `/source remove <chat_id>`
- `/source list`

## Statistics

Firebase tracks:
- total users
- active users (activity within `ACTIVE_USER_DAYS`)
- total video requests
- successful batches
- failed requests
- videos delivered
- video failures
- source count / enabled source count
- broadcast runs
- broadcast success/failure

Per-user activity also records recent events under `activity/<user_id>`.

## Firebase structure

```text
users/
sources/
cleanup/
activity/
stats/
broadcasts/
```

No video files are stored in Firebase.

## 10-minute cooldown

The cooldown is stored as an ISO timestamp in:

```text
users/<USER_ID>/cooldown_until
```

If the user presses `🎬 Video File` before the timestamp, no new videos are sent.

## Important Telegram requirement

The Telegram Bot must have access to every configured source channel/chat. The Telethon account must also be legitimately authorized to read the source history.

`copyMessage` copies the Telegram message server-side; the Render process does not download the media.

Content protection can restrict Telegram forwarding/saving controls, but it cannot technically prevent screenshots or external recording.

## Environment

Required:
- `BOT_TOKEN`
- `OWNER_IDS`
- `API_ID`
- `API_HASH`
- `SESSION_BASE64` or first-login `PHONE_NUMBER`
- `FIREBASE_DATABASE_URL`
- `FIREBASE_CREDENTIALS_JSON`

Recommended:
- `VIDEOS_PER_REQUEST=5`
- `VIDEO_COOLDOWN_MINUTES=10`
- `AUTO_DELETE_HOURS=2`
- `ACTIVE_USER_DAYS=30`

## Deployment

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
python bot.py
```

Never commit Telegram session files or Firebase service-account credentials.
