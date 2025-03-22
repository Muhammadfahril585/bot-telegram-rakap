
import os
import sqlite3
import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, CallbackContext
)

# Inisialisasi Flask
app = Flask(__name__)

# Token bot Telegram
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Error: TELEGRAM_TOKEN belum diatur di environment variables.")

# URL webhook (gantilah dengan URL server kamu)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Pastikan kamu sudah mengatur ini di environment

# Koneksi ke database SQLite
conn = sqlite3.connect("hafalan.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS santri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT,
                    pekan INTEGER,
                    bulan TEXT,
                    hafalan_baru INTEGER,
                    total_juz REAL)''')
conn.commit()

# Inisialisasi bot dengan webhook
app_telegram = Application.builder().token(TOKEN).build()

# Fungsi menangani start
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("1️⃣ Tambah Hafalan", callback_data="tambah_hafalan")],
        [InlineKeyboardButton("2️⃣ Lihat Hafalan", callback_data="lihat_hafalan")],
        [InlineKeyboardButton("3️⃣ Rekap Pekanan", callback_data="rekap_pekanan")],
        [InlineKeyboardButton("4️⃣ Edit Hafalan", callback_data="edit_hafalan")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔹 *Menu Bot Hafalan*", reply_markup=reply_markup, parse_mode="Markdown")

# Fungsi menangani menu
async def menu_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    menu_responses = {
        "tambah_hafalan": "📌 Kirim data dengan format:\nTambahHafalan; Nama Santri; Hafalan Baru (halaman); Total Hafalan (juz)",
        "lihat_hafalan": "🔍 Kirim nama santri untuk melihat data hafalannya.",
        "rekap_pekanan": "📊 Kirim nama santri untuk melihat rekap hafalannya dalam sebulan.",
        "edit_hafalan": "✏️ Kirim data dengan format:\nEditHafalan; Nama Santri; Pekan; Hafalan Baru (halaman); Total Hafalan (juz)"
    }
    await query.message.reply_text(menu_responses.get(query.data, "Perintah tidak dikenali."))

# Fungsi menangani webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), app_telegram.bot)
    app_telegram.update_queue.put(update)
    return "OK", 200

# Fungsi untuk mengatur webhook di Telegram
async def set_webhook():
    await app_telegram.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

# Fungsi utama menjalankan bot
def main():
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CallbackQueryHandler(menu_handler))
    
    # Menjalankan webhook
    print("Mengatur webhook...")
    app_telegram.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(set_webhook())  # Mengatur webhook sebelum bot berjalan
    main()
