
import os
import sqlite3
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, CallbackContext
)
import asyncio

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)

# Inisialisasi Flask
app = Flask(__name__)

# Token bot Telegram
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("Error: TELEGRAM_TOKEN belum diatur di environment variables.")
if not WEBHOOK_URL:
    raise ValueError("Error: WEBHOOK_URL belum diatur di environment variables.")

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

# Inisialisasi bot
app_telegram = Application.builder().token(TOKEN).build()

# Fungsi menampilkan menu utama
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("1️⃣ Tambah Hafalan", callback_data="tambah_hafalan")],
        [InlineKeyboardButton("2️⃣ Lihat Hafalan", callback_data="lihat_hafalan")],
        [InlineKeyboardButton("3️⃣ Rekap Pekanan", callback_data="rekap_pekanan")],
        [InlineKeyboardButton("4️⃣ Edit Hafalan", callback_data="edit_hafalan")],
        [InlineKeyboardButton("5️⃣ Riwayat Hafalan", callback_data="riwayat_hafalan")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔹 *Menu Bot Hafalan*", reply_markup=reply_markup, parse_mode="Markdown")

# Route untuk webhook (menerima update dari Telegram)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON received"}), 400
        
        update = Update.de_json(data, app_telegram.bot)
        asyncio.run(app_telegram.process_update(update))

        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Fungsi untuk mengatur webhook di Telegram
async def set_webhook():
    url = f"{WEBHOOK_URL}/{TOKEN}"
    await app_telegram.bot.set_webhook(url)
    logging.info(f"Webhook telah diatur: {url}")

# Fungsi utama menjalankan bot
async def main():
    app_telegram.add_handler(CommandHandler("start", start))

    print("Mengatur webhook...")
    await set_webhook()

    # Menjalankan Flask untuk menangani webhook
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    asyncio.run(main())
