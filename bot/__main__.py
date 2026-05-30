import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from bot.config import BOT_TOKEN, TIMEZONE
from bot.handlers.admin import add_user, remove_user, list_users
from bot.handlers.user_commands import start, help_command, saldo, laporan, batal
from bot.handlers.messages import handle_message
from bot.database.connection import init_db
from bot.database.queries import reset_daily_limits
from scripts.backup_db import backup_database

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def _scheduled_reset():
    reset_daily_limits()
    backup_database()
    logging.info("Daily rate limits reset and database backed up.")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set. Check your .env file.")

    init_db()

    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(_scheduled_reset, "cron", hour=0, minute=0)
    scheduler.start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(CommandHandler("batal", batal))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(CommandHandler("remove", remove_user))
    app.add_handler(CommandHandler("listuser", list_users))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Fintra bot started")
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
