from telegram import Update
from telegram.ext import ContextTypes
from bot.config import SUPERADMIN_ID
from bot.database import queries
from bot.services.rate_limiter import get_daily_usage

async def _ensure_superadmin(update: Update) -> bool:
    user_id = str(update.effective_user.id)
    if user_id != SUPERADMIN_ID:
        await update.message.reply_text("⛔ Akses ditolak. Hanya Superadmin yang dapat menggunakan perintah ini.")
        return False
    return True

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_superadmin(update):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /add <telegram_id> [username]")
        return
    telegram_id = args[0]
    username = args[1] if len(args) > 1 else "unknown"
    queries.add_user(telegram_id, username, "user")
    await update.message.reply_text(f"✅ Pengguna {telegram_id} telah ditambahkan ke whitelist.")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_superadmin(update):
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /remove <telegram_id>")
        return
    telegram_id = args[0]
    if telegram_id == SUPERADMIN_ID:
        await update.message.reply_text("⛔ Tidak dapat menghapus Superadmin.")
        return
    queries.remove_user(telegram_id)
    await update.message.reply_text(f"✅ Pengguna {telegram_id} telah dihapus dari whitelist.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_superadmin(update):
        return
    users = queries.list_users()
    if not users:
        await update.message.reply_text("Tidak ada pengguna terdaftar.")
        return
    lines = ["📋 <b>Daftar Pengguna Terdaftar:</b>\n"]
    for u in users:
        lines.append(f"• <code>{u['telegram_id']}</code> | @{u['username']} | {u['role']} | Kuota: {u['daily_usage']}/50")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
