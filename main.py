
import os
import sqlite3
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, CallbackContext
)
import asyncio

# Inisialisasi Flask
app = Flask(__name__)

# Token bot Telegram & URL Webhook dari environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("Error: TELEGRAM_TOKEN atau WEBHOOK_URL belum diatur.")

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

# Inisialisasi bot Telegram dengan mode asinkron
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

# Tambahkan handler ke bot
app_telegram.add_handler(CommandHandler("start", start))

# Endpoint untuk webhook (harus memakai await saat memproses update)
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(), app_telegram.bot)
        await app_telegram.process_update(update)  # Perbaikan: pakai await
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error di webhook: {str(e)}")  # Logging tambahan
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint untuk cek status bot
@app.route("/", methods=["GET"])
def home():
    return "Bot Telegram Hafalan Qur'an Aktif!", 200

# Fungsi mengatur webhook di Telegram
async def set_webhook():
    await app_telegram.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

# Fungsi utama menjalankan bot
async def main():
    print("Mengatur webhook...")
    await set_webhook()
    app.run(host="0.0.0.0", port=8080)

# Jalankan aplikasi dengan asyncio
if __name__ == "__main__":
    import uvicorn
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    uvicorn.run(app, host="0.0.0.0", port=8080)
