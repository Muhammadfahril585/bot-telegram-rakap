
import os
import sqlite3
import asyncio
import threading
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, CallbackContext
)

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

# Fungsi menangani webhook
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(), app_telegram.bot)
        asyncio.create_task(app_telegram.process_update(update))  # Menjalankan pemrosesan secara async
        return "OK", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

# Fungsi untuk mengatur webhook di Telegram
async def set_webhook():
    await app_telegram.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

# Fungsi untuk menjalankan Flask di thread terpisah
def run_flask():
    app.run(host="0.0.0.0", port=8080, threaded=True)

# Fungsi utama menjalankan bot
async def main():
    app_telegram.add_handler(CommandHandler("start", start))

    print("Mengatur webhook...")
    await set_webhook()

    # Menjalankan Flask di thread lain
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Menjaga loop tetap berjalan
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
