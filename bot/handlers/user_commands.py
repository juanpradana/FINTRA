from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database import queries
from bot.database.queries import ensure_superadmin
from bot.config import SUPERADMIN_ID, SUPERADMIN_USERNAME
import pytz
from bot.config import TIMEZONE

_COMMON_BUTTONS = [["/saldo", "/laporan"], ["/batal", "/help"]]
_SUPERADMIN_BUTTONS = [["/add", "/remove", "/listuser"], ["/saldo", "/laporan"], ["/batal", "/help"]]

def _get_keyboard(user_id: str) -> ReplyKeyboardMarkup:
    is_super = user_id == SUPERADMIN_ID
    return ReplyKeyboardMarkup(
        _SUPERADMIN_BUTTONS if is_super else _COMMON_BUTTONS,
        resize_keyboard=True,
    )

def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_superadmin(SUPERADMIN_ID, SUPERADMIN_USERNAME)
    user_id = str(user.id)
    if not queries.is_whitelisted(user_id):
        await update.message.reply_text("⛔ Anda belum terdaftar di Fintra. Hubungi Superadmin untuk mendapatkan akses.")
        return
    await update.message.reply_text(
        f"👋 Selamat datang di <b>Fintra</b>, {_esc(user.first_name)}!\n\n"
        "Cukup ketik pesan teks biasa untuk mencatat transaksi keuangan.\n"
        "Contoh: <i>'beli bakso 25 ribu tadi siang'</i>\n\n"
        "Gunakan tombol di bawah untuk perintah cepat.",
        parse_mode="HTML",
        reply_markup=_get_keyboard(user_id),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not queries.is_whitelisted(user_id):
        return
    await update.message.reply_text(
        "ℹ️ <b>Fintra Help Desk &amp; Documentation</b>\n\n"
        "Cukup ketik pesan teks biasa tanpa command untuk mencatat keuangan secara otomatis.\n\n"
        "🔒 <b>Batasan Penggunaan (Anti-Spam):</b>\n"
        "• Maksimal 5 pesan / menit.\n"
        "• Maksimal 50 transaksi / hari.\n\n"
        "💡 <b>Contoh Input:</b>\n"
        "• <i>'beli bakso 25 ribu tadi siang'</i>\n"
        "• <i>'kemarin sore bayar cicilan motor 1.5 juta'</i>\n\n"
        "📂 <b>Kategori Valid:</b>\n"
        "<code>makanan</code>, <code>transportasi</code>, <code>hiburan</code>, <code>tagihan</code>, <code>investasi</code>, <code>lainnya</code>.\n\n"
        "🛠️ <b>Daftar Perintah:</b>\n"
        "/saldo - Cek akumulasi sisa dana saat ini.\n"
        "/laporan - Unduh rekap laporan Excel &amp; PDF bulan berjalan.\n"
        "/batal - Menghapus catatan transaksi terakhir Anda.\n"
        "---------------------------------------\n"
        "✒️ <i>Fintra Version 1.6 | Created by Farzani R.B.A.</i>",
        parse_mode="HTML",
        reply_markup=_get_keyboard(user_id),
    )

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not queries.is_whitelisted(user_id):
        return
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    balance = queries.get_balance(user_id, now.year, now.month)
    formatted = f"Rp{balance:,}".replace(",", ".")
    month_name = now.strftime("%B %Y")
    await update.message.reply_text(f"💰 <b>Saldo {month_name}:</b> {formatted}", parse_mode="HTML")

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

    await update.message.reply_text("📊 Menyusun laporan...")

    from bot.services.llm_client import generate_report_analysis
    category_summary = queries.get_category_summary(user_id, now.year, now.month)
    month_name = now.strftime("%B %Y")
    analysis = generate_report_analysis(summary, category_summary, month_name)
    await update.message.reply_text(f"🧠 <b>Analisis Keuangan {month_name}</b>\n\n{analysis}", parse_mode="HTML")

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
    formatted = f"Rp{last['nominal']:,}".replace(",", ".")
    await update.message.reply_text(
        f"✅ Transaksi terakhir berhasil dibatalkan:\n"
        f"• {last['type'].capitalize()}: {formatted} ({last['category']})"
    )
