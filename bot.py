import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from handlers.start import start_cmd, consent_callback, language_callback
from handlers.user import video_button, help_button, auto_delete_worker
from handlers.admin import admin_command, admin_callback
from handlers.sources import source_command

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("video-bot")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    from telegram_client import TelegramSourceClient
    client = TelegramSourceClient()
    await client.start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["source_client"] = client

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_button))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("source", source_command))

    app.add_handler(CallbackQueryHandler(consent_callback, pattern=r"^(agree|disagree)$"))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang:"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^adm:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, video_button))

    delete_task = asyncio.create_task(auto_delete_worker(app))
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        log.info("Bot is running.")
        await asyncio.Event().wait()
    finally:
        delete_task.cancel()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
