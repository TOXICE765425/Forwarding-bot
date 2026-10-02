import asyncio
import logging
import os
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN

from handlers.start import (
    start_cmd,
    consent_callback,
    language_callback,
)

from handlers.user import (
    video_button,
    auto_delete_worker,
)

from handlers.admin import (
    bot_command,
    admin_command,
    admin_callback,
    stats_command,
    user_command,
    activity_command,
    bots_command,
    help_command,
)

from handlers.broadcast import broadcast_command

from handlers.sources import source_command


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

log = logging.getLogger("video-bot")


# =========================
# RENDER HEALTH SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler,
    )

    log.info("Health server running on port %s", port)

    server.serve_forever()


# Start Render health server
health_thread = threading.Thread(
    target=start_health_server,
    daemon=True,
)

health_thread.start()


# =========================
# MAIN BOT
# =========================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    # Start Telethon source client
    from telegram_client import TelegramSourceClient

    client = TelegramSourceClient()

    await client.start()

    # Telegram Bot
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.bot_data["source_client"] = client

    # =========================
    # COMMAND HANDLERS
    # =========================

    app.add_handler(
        CommandHandler("start", start_cmd)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("admin", admin_command)
    )

    app.add_handler(
        CommandHandler("bot", bot_command)
    )

    app.add_handler(
        CommandHandler("source", source_command)
    )

    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("user", user_command))
    app.add_handler(CommandHandler("activity", activity_command))
    app.add_handler(CommandHandler("bots", bots_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    # =========================
    # CALLBACK HANDLERS
    # =========================

    app.add_handler(
        CallbackQueryHandler(
            consent_callback,
            pattern=r"^(agree|disagree)$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            language_callback,
            pattern=r"^lang:",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^adm:",
        )
    )

    # =========================
    # TEXT HANDLER
    # =========================

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            video_button,
        )
    )

    # =========================
    # AUTO DELETE WORKER
    # =========================

    delete_task = asyncio.create_task(
        auto_delete_worker(app)
    )

    try:

        await app.initialize()

        await app.start()

        await app.updater.start_polling(
            drop_pending_updates=True
        )

        log.info("Bot is running.")

        # Keep application alive
        await asyncio.Event().wait()

    finally:

        delete_task.cancel()

        try:
            await delete_task
        except asyncio.CancelledError:
            pass

        await app.updater.stop()

        await app.stop()

        await app.shutdown()

        await client.stop()


# =========================
# START
# =========================

if __name__ == "__main__":
    asyncio.run(main())
