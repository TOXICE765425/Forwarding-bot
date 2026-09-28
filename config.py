import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

OWNER_IDS = {
    int(x.strip())
    for x in os.getenv("OWNER_IDS", "").split(",")
    if x.strip().isdigit()
}

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_NAME = os.getenv(
    "SESSION_NAME",
    "sessions/source_client"
).strip()

# Base64 encoded Telethon .session file.
# Used on Render/other hosted platforms where the session
# file is not committed to GitHub.
SESSION_BASE64 = os.getenv("SESSION_BASE64", "").strip()

PHONE_NUMBER = os.getenv("PHONE_NUMBER", "").strip()

FIREBASE_DATABASE_URL = os.getenv(
    "FIREBASE_DATABASE_URL",
    ""
).strip()

FIREBASE_CREDENTIALS_JSON = os.getenv(
    "FIREBASE_CREDENTIALS_JSON",
    ""
).strip()

FIREBASE_CREDENTIALS_FILE = os.getenv(
    "FIREBASE_CREDENTIALS_FILE",
    ""
).strip()

VIDEOS_PER_REQUEST = int(
    os.getenv("VIDEOS_PER_REQUEST", "5")
)

AUTO_DELETE_HOURS = int(
    os.getenv("AUTO_DELETE_HOURS", "2")
)

HISTORY_PAGE_SIZE = int(
    os.getenv("HISTORY_PAGE_SIZE", "100")
)

DEFAULT_LANGUAGE = "hi"

BOT_NAME = os.getenv(
    "BOT_NAME",
    "Video Bot"
)

# Comma-separated Telegram chat IDs.
# Example:
# -1001234567890,-1009876543210
INITIAL_SOURCE_IDS = [
    int(x.strip())
    for x in os.getenv("INITIAL_SOURCE_IDS", "").split(",")
    if x.strip().lstrip("-").isdigit()
]
