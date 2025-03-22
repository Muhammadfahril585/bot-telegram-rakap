
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

# Fungsi menangani klik tombol menu
async def menu_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "riwayat_hafalan":
        # Ambil daftar bulan unik dari database
        cursor.execute("SELECT DISTINCT bulan FROM santri ORDER BY bulan DESC")
        bulan_list = cursor.fetchall()

        if not bulan_list:
            await query.message.reply_text("⚠️ Tidak ada data riwayat hafalan.")
            return

        keyboard = [[InlineKeyboardButton(bulan[0], callback_data=f"bulan_{bulan[0]}")] for bulan in bulan_list]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("📅 Pilih bulan untuk melihat riwayat hafalan:", reply_markup=reply_markup)

    elif query.data.startswith("bulan_"):
        bulan_terpilih = query.data.replace("bulan_", "")

        cursor.execute("SELECT nama, pekan, hafalan_baru, total_juz FROM santri WHERE bulan=? ORDER BY pekan", (bulan_terpilih,))
        hasil = cursor.fetchall()

        if not hasil:
            await query.message.reply_text(f"⚠️ Tidak ada data hafalan untuk bulan *{bulan_terpilih}*.", parse_mode="Markdown")
            return

        pesan = f"📅 *Riwayat Hafalan Bulan {bulan_terpilih}*:\n"
        for nama, pekan, hafalan_baru, total_juz in hasil:
            total_juz_str = int(total_juz) if total_juz.is_integer() else total_juz
            pesan += f"\n👤 {nama}\n📅 Pekan {pekan}\n📖 Hafalan Baru: {hafalan_baru} Halaman\n📚 Total Hafalan: {total_juz_str} Juz\n"

        await query.message.reply_text(pesan, parse_mode="Markdown")

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
