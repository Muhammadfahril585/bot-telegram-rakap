
import os
import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Ambil token dari environment variable
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("Error: TELEGRAM_TOKEN belum diatur.")

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

# Inisialisasi bot Telegram
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

# Fungsi utama menjalankan bot dengan polling
async def main():
    print("Bot berjalan dengan metode polling...")
    await app_telegram.initialize()
    await app_telegram.start()
    app_telegram.run_polling()

# Jalankan aplikasi dengan asyncio
if __name__ == "__main__":
    asyncio.run(main())  # Gunakan asyncio.run untuk menghindari error loop
