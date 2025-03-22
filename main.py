
import os
import sqlite3
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from flask import Flask
from threading import Thread

# Fungsi untuk menjaga bot tetap berjalan (hanya untuk Replit, tidak dibutuhkan di Render)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Mengambil token dari environment variable
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Error: TELEGRAM_TOKEN belum diatur di environment variables.")

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

# Fungsi tambah hafalan
async def tambah_hafalan(update: Update, context: CallbackContext) -> None:
    try:
        pesan = update.message.text
        if not pesan.startswith("TambahHafalan;"):
            return  

        parts = pesan.split(";")
        if len(parts) != 4:
            await update.message.reply_text("⚠️ Format salah! Gunakan format:\nTambahHafalan; Nama Santri; Hafalan Baru (halaman); Total Hafalan (juz)")
            return

        nama = parts[1].strip()
        hafalan_baru = int(parts[2].strip())  
        total_juz = float(parts[3].strip())

        bulan_sekarang = datetime.datetime.now().strftime("%B %Y")

        cursor.execute("SELECT pekan, bulan FROM santri WHERE nama=? ORDER BY pekan DESC LIMIT 1", (nama,))
        hasil = cursor.fetchone()

        pekan = 1 if not hasil or hasil[1] != bulan_sekarang else hasil[0] + 1

        cursor.execute("INSERT INTO santri (nama, pekan, bulan, hafalan_baru, total_juz) VALUES (?, ?, ?, ?, ?)", 
                       (nama, pekan, bulan_sekarang, hafalan_baru, total_juz))
        conn.commit()

        total_juz_str = int(total_juz) if total_juz.is_integer() else total_juz

        if pekan == 4:
            cursor.execute("SELECT SUM(hafalan_baru) FROM santri WHERE nama=? AND bulan=?", (nama, bulan_sekarang))
            total_hafalan_baru = cursor.fetchone()[0]
            await update.message.reply_text(f"✅ Data lengkap 4 pekan!\nNama: {nama}\nTotal Hafalan Baru (4 pekan): {total_hafalan_baru} Halaman")
        else:
            await update.message.reply_text(f"✅ Data disimpan!\nNama: {nama}\nPekan: {pekan}\nBulan: {bulan_sekarang}\nHafalan Baru: {hafalan_baru} Halaman\nTotal Hafalan: {total_juz_str} Juz")
    
    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}")

# Fungsi melihat data santri
async def lihat_santri(update: Update, context: CallbackContext) -> None:
    nama = update.message.text.strip()
    cursor.execute("SELECT pekan, bulan, hafalan_baru, total_juz FROM santri WHERE nama=? ORDER BY bulan DESC, pekan DESC", (nama,))
    hasil = cursor.fetchall()

    if not hasil:
        await update.message.reply_text("⚠️ Data tidak ditemukan!")
        return

    pesan = f"📌 Data hafalan {nama}:\n"
    for pekan, bulan, hafalan_baru, total_juz in hasil:
        total_juz_str = int(total_juz) if total_juz.is_integer() else total_juz
        pesan += f"\n📅 Pekan {pekan} - {bulan}\n📖 Hafalan Baru: {hafalan_baru} Halaman\n📚 Total Hafalan: {total_juz_str} Juz\n"

    await update.message.reply_text(pesan)

# Fungsi mengedit hafalan
async def edit_hafalan(update: Update, context: CallbackContext) -> None:
    try:
        pesan = update.message.text
        if not pesan.startswith("EditHafalan;"):
            return  

        parts = pesan.split(";")
        if len(parts) != 5:
            await update.message.reply_text("⚠️ Format salah! Gunakan format:\nEditHafalan; Nama Santri; Pekan; Hafalan Baru (halaman); Total Hafalan (juz)")
            return

        nama = parts[1].strip()
        pekan = int(parts[2].strip())
        hafalan_baru = int(parts[3].strip())
        total_juz = float(parts[4].strip())

        cursor.execute("SELECT * FROM santri WHERE nama=? AND pekan=?", (nama, pekan))
        if cursor.fetchone() is None:
            await update.message.reply_text("⚠️ Data tidak ditemukan untuk diedit!")
            return

        cursor.execute("UPDATE santri SET hafalan_baru=?, total_juz=? WHERE nama=? AND pekan=?", 
                       (hafalan_baru, total_juz, nama, pekan))
        conn.commit()

        total_juz_str = int(total_juz) if total_juz.is_integer() else total_juz
        await update.message.reply_text(f"✅ Data diperbarui!\nNama: {nama}\nPekan: {pekan}\nHafalan Baru: {hafalan_baru} Halaman\nTotal Hafalan: {total_juz_str} Juz")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}")

# Fungsi perintah `/start`
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Halo! Kirim data hafalan santri dengan format:\n"
        "TambahHafalan; Nama Santri; Hafalan Baru (halaman); Total Hafalan (juz)\n\n"
        "Edit data dengan format:\n"
        "EditHafalan; Nama Santri; Pekan; Hafalan Baru (halaman); Total Hafalan (juz)\n\n"
        "Untuk melihat data, cukup kirimkan nama santri."
    )

# Fungsi utama menjalankan bot
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^TambahHafalan;"), tambah_hafalan))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^EditHafalan;"), edit_hafalan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lihat_santri))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    keep_alive()  # Hanya aktif jika perlu "keep alive"
    main()
