from telegram import Update
from telegram.ext import ContextTypes
from bot.database import queries
from bot.services.rate_limiter import check_burst, check_daily, record_request, is_admin_command
from bot.services.gemini_client import parse_transaction

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text.strip()

    if not queries.is_whitelisted(user_id):
        return

    if not check_burst(user_id):
        await update.message.reply_text("⚠️ **Mencatat Terlalu Cepat!** Batas maksimal input adalah 5 pesan per menit untuk menjaga stabilitas sistem. Silakan tunggu beberapa saat lagi.", parse_mode="Markdown")
        return

    if not check_daily(user_id):
        await update.message.reply_text("⚠️ **Kuota Harian Habis!** Anda telah mencapai batas 50 transaksi hari ini. Silakan tunggu hingga reset pukul 00:00 WIB.", parse_mode="Markdown")
        return

    result = parse_transaction(text)

    if "error" in result:
        if result["error"] == "out_of_domain":
            await update.message.reply_text("❌ **Akses Ditolak.** Sistem Fintra hanya menerima input terkait pencatatan transaksi keuangan dan analisis anggaran.", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ Maaf, terjadi kesalahan saat memproses pesan Anda. Silakan coba lagi.")
        return

    queries.insert_transaction(
        telegram_id=user_id,
        type_=result["type"],
        nominal=result["nominal"],
        category=result["category"],
        note=result.get("note", ""),
        transaction_date=result["transaction_date"],
    )

    record_request(user_id)

    formatted_nominal = f"Rp{result['nominal']:,}".replace(",", ".")
    emoji = "📥" if result["type"] == "pemasukan" else "📤"
    await update.message.reply_text(
        f"{emoji} **Transaksi Tercatat!**\n"
        f"• {result['type'].capitalize()}: {formatted_nominal}\n"
        f"• Kategori: {result['category']}\n"
        f"• Tanggal: {result['transaction_date']}",
        parse_mode="Markdown",
    )
