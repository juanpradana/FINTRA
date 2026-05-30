from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import queries
from bot.database.queries import ensure_superadmin
from bot.config import SUPERADMIN_ID, SUPERADMIN_USERNAME
import pytz
from bot.config import TIMEZONE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_superadmin(SUPERADMIN_ID, SUPERADMIN_USERNAME)
    if not queries.is_whitelisted(str(user.id)):
        await update.message.reply_text("⛔ Anda belum terdaftar di Fintra. Hubungi Superadmin untuk mendapatkan akses.")
        return
    await update.message.reply_text(
        f"👋 Selamat datang di **Fintra**, {user.first_name}!\n\n"
        "Cukup ketik pesan teks biasa untuk mencatat transaksi keuangan.\n"
        "Contoh: *'beli bakso 25 ribu tadi siang'*\n\n"
        "Ketik /help untuk bantuan lebih lanjut.",
        parse_mode="Markdown",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not queries.is_whitelisted(str(update.effective_user.id)):
        return
    await update.message.reply_text(
        "ℹ️ **Fintra Help Desk & Documentation**\n\n"
        "Cukup ketik pesan teks biasa tanpa command untuk mencatat keuangan secara otomatis.\n\n"
        "🔒 **Batasan Penggunaan (Anti-Spam):**\n"
        "• Maksimal 5 pesan / menit.\n"
        "• Maksimal 50 transaksi / hari.\n\n"
        "💡 **Contoh Input:**\n"
        "• *'beli bakso 25 ribu tadi siang'*\n"
        "• *'kemarin sore bayar cicilan motor 1.5 juta'*\n\n"
        "📂 **Kategori Valid:**\n"
        "`makanan`, `transportasi`, `hiburan`, `tagihan`, `investasi`, `lainnya`.\n\n"
        "🛠️ **Daftar Perintah:**\n"
        "/saldo - Cek akumulasi sisa dana saat ini.\n"
        "/laporan - Unduh rekap laporan Excel & PDF bulan berjalan.\n"
        "/batal - Menghapus catatan transaksi terakhir Anda.\n"
        "---------------------------------------\n"
        "✒️ *Fintra Version 1.6 | Created by Farzani R.B.A.*",
        parse_mode="Markdown",
    )

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not queries.is_whitelisted(user_id):
        return
    balance = queries.get_balance(user_id)
    formatted = f"Rp{balance:,}".replace(",", ".")
    await update.message.reply_text(f"💰 **Saldo Anda:** {formatted}", parse_mode="Markdown")

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not queries.is_whitelisted(user_id):
        return
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    transactions = queries.get_monthly_transactions(user_id, now.year, now.month)
    if not transactions:
        await update.message.reply_text("📭 Belum ada transaksi bulan ini.")
        return
    summary = queries.get_monthly_summary(user_id, now.year, now.month)
    username = update.effective_user.first_name or "User"

    from bot.services.report import generate_excel, generate_pdf
    import tempfile, os

    xlsx_path = os.path.join(tempfile.gettempdir(), f"fintra_{user_id}_{now.strftime('%Y%m')}.xlsx")
    pdf_path = os.path.join(tempfile.gettempdir(), f"fintra_{user_id}_{now.strftime('%Y%m')}.pdf")

    generate_excel(xlsx_path, transactions, summary, username, now)
    generate_pdf(pdf_path, transactions, summary, username, now)

    await update.message.reply_document(document=open(xlsx_path, "rb"), filename=f"laporan_{now.strftime('%Y%m')}.xlsx")
    await update.message.reply_document(document=open(pdf_path, "rb"), filename=f"laporan_{now.strftime('%Y%m')}.pdf")

    os.remove(xlsx_path)
    os.remove(pdf_path)

async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not queries.is_whitelisted(user_id):
        return
    last = queries.get_last_transaction(user_id)
    if not last:
        await update.message.reply_text("📭 Tidak ada transaksi yang bisa dibatalkan.")
        return
    queries.delete_transaction(last["id"], user_id)
    await update.message.reply_text(
        f"✅ Transaksi terakhir berhasil dibatalkan:\n"
        f"• {last['type'].capitalize()}: Rp{last['nominal']:,} ({last['category']})"
        .replace(",", "."),
        parse_mode="Markdown",
    )
