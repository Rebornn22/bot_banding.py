import telebot
import logging
import smtplib
import imaplib
import email
import time
import threading
from email.message import EmailMessage

# =====================================================================
# 1. PENGATURAN AWAL (GANTI BAGIAN INI DENGAN DATA ANDA)
# =====================================================================
API_TOKEN = '8999643420:AAGHq2ZPJOY3vDUDQeq5fKppPvrpnhyi-Gc'  # Dari @BotFather
ADMIN_ID = 5086913598                  # ID Telegram Anda (tanpa tanda petik)

# Pengaturan Gmail & Tujuan Email
GMAIL_PENGIRIM = 'xsociety936@gmail.com'     # Email Gmail Anda sebagai pengirim
GMAIL_PASSWORD = 'jctheglcendykfao'       # 16 Karakter Sandi Aplikasi Google Anda
EMAIL_PENERIMA = 'support@support.whatsapp.com'   # Email target/tujuan banding
# =====================================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
bot = telebot.TeleBot(API_TOKEN)

print("=== BOT TELEGRAM (MONITOR BALASAN GMAIL) AKTIF ===")
print("Menunggu input nomor HP...")

def kirim_via_gmail(nomor_hp, isi_pesan):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Account Login Restriction Appeal - {nomor_hp}"
        msg['From'] = GMAIL_PENGIRIM
        msg['To'] = EMAIL_PENERIMA
        msg.set_content(isi_pesan)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_PENGIRIM, GMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Gagal mengirim email lewat Gmail: {e}")
        return False

def cek_balasan_gmail(chat_id, nomor_hp):
    print(f"Memulai monitoring balasan Gmail untuk nomor: {nomor_hp}")
    for _ in range(30):
        time.sleep(60)
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_PENGIRIM, GMAIL_PASSWORD)
            mail.select("inbox")

            status, data = mail.search(None, f'(UNSEEN FROM "{EMAIL_PENERIMA}")')
            mail_ids = data[0].split()
            
            if mail_ids:
                latest_id = mail_ids[-1]
                status, bytes_data = mail.fetch(latest_id, '(RFC822)')
                
                for response_part in bytes_data:
                    if isinstance(response_part, tuple):
                        email_message = email.message_from_bytes(response_part[1])
                        subjek = email_message['subject']
                        
                        notif_teks = (
                            f"🔔 **PEMBERITAHUAN BALASAN GMAIL** 🔔\n\n"
                            f"Email banding untuk nomor `{nomor_hp}` **SUDAH DIBALAS** oleh ({EMAIL_PENERIMA})!\n\n"
                            f"📧 Subjek Balasan: *{subjek}*\n"
                            f"Silakan buka aplikasi Gmail Anda untuk membaca isi lengkap balasannya."
                        )
                        bot.send_message(chat_id, notif_teks, parse_mode="Markdown")
                        
                        # PERBAIKAN WARNING: Ditambahkan huruf r di depan '\Seen'
                        mail.store(latest_id, '+FLAGS', r'\Seen')
                        mail.logout()
                        return 

            mail.logout()
        except Exception as e:
            print(f"Error saat mengecek inbox Gmail: {e}")
            
    print(f"Monitoring Gmail selesai untuk nomor {nomor_hp} (Waktu tunggu habis).")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Maaf, bot ini bersifat pribadi.")
        return
    bot.reply_to(message, "Halo! Bot Gmail siap. Kirim nomor HP untuk membuat teks banding baru.")

@bot.message_handler(func=lambda message: True)
def proses_nomor_hp(message):
    if message.from_user.id != ADMIN_ID:
        return

    nomor_hp = message.text.strip()

    teks_banding = (
        f"I am writing to appeal the login restriction placed on my account. "
        f"I am currently unable to access my account due to a security restriction, "
        f"as indicated in the notification.\n\n"
        f"I believe this restriction is a mistake, as I have always used my account "
        f"normally and strictly followed all community guidelines. Therefore, I would "
        f"kindly request a review of my account and your assistance in restoring my access.\n\n"
        f"Here are my details for verification:\n"
        f"Phone number associated with the account: [{nomor_hp}]\n\n"
        f"I am fully prepared to complete any additional verification steps if required. "
        f"Thank you very much for your time, consideration, and support. "
        f"I look forward to your assistance."
    )

    bot.reply_to(message, teks_banding)
    status_msg = bot.send_message(message.chat.id, "⏳ Sedang mengirim pesan lewat Gmail...")

    sukses_email = kirim_via_gmail(nomor_hp, teks_banding)

    if sukses_email:
        bot.edit_message_text(f"✅ Sukses terkirim menggunakan Gmail ke: {EMAIL_PENERIMA}\n\n"
                              f"🔍 _Bot otomatis memonitor inbox Gmail Anda selama 30 menit ke depan. "
                              f"Anda akan menerima notifikasi jika ada email balasan masuk._", 
                              message.chat.id, status_msg.message_id, parse_mode="Markdown")
        
        monitor_thread = threading.Thread(target=cek_balasan_gmail, args=(message.chat.id, nomor_hp))
        monitor_thread.daemon = True
        monitor_thread.start()
        
    else:
        bot.edit_message_text("❌ Gagal mengirim via Gmail. Periksa kembali konfigurasi atau koneksi server.", message.chat.id, status_msg.message_id)

if __name__ == '__main__':
    try:
        # Menghapus tumpukan pesan lama dan mencegah tabrakan instansi
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Terjadi kesalahan pada bot: {e}")