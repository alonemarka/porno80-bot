import telebot
import sqlite3
import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import time
import os

# ================== AYARLAR ==================
TOKEN = os.getenv("TOKEN") or "8900271780:AAGJ--CtEgxPbQcMJ1mspBxbTd1ZZ3iH6p8"
MINI_APP_URL = "https://www.porno80.net/"   

CHANNEL_USERNAME = "@pxrno80duyuru"      
GROUP_USERNAME = "@atattv44yedek"        

ADMIN_IDS = [8064250098]             

bot = telebot.TeleBot(TOKEN)

# ================== VERİTABANI ==================
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    is_vip INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0,
    join_date TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS keys (
    key TEXT PRIMARY KEY,
    used_by INTEGER,
    used_date TEXT
)''')

conn.commit()

# ================== YARDIMCI FONKSİYONLAR ==================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_banned(user_id):
    c.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    return result and result[0] == 1

def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return False

def check_group_membership(user_id):
    if GROUP_USERNAME is None:
        return True
    try:
        member = bot.get_chat_member(GROUP_USERNAME, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return False

def has_full_access(user_id):
    if is_banned(user_id):
        return False
    return check_channel_membership(user_id) and check_group_membership(user_id)

# ================== START ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    if is_banned(user_id):
        return bot.send_message(message.chat.id, "⛔ Bu botu kullanmaktan yasaklandınız.")

    c.execute("""INSERT OR IGNORE INTO users 
                 (user_id, username, first_name, join_date) 
                 VALUES (?,?,?,?)""",
              (user_id, username, first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

    if not check_channel_membership(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanala Katıl", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        return bot.send_message(message.chat.id, "❗ Botu kullanmak için **kanala** katılmalısın!", reply_markup=markup, parse_mode='Markdown')

    if not check_group_membership(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("👥 Gruba Katıl", url=f"https://t.me/{GROUP_USERNAME[1:]}"))
        return bot.send_message(message.chat.id, "❗ Botu kullanmak için **sohbet grubuna** da katılmalısın!", reply_markup=markup, parse_mode='Markdown')

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🎥 Videoları Gör", callback_data="open_mini_app"))
    markup.add(InlineKeyboardButton("👤 Bilgilerim", callback_data="user_info"))

    text = f"""🔥 **Porno Videoları Dünyasına Hoş Geldiniz!** 🔥

Merhaba {first_name}!

✅ Kanala ve gruba katıldığın için teşekkürler.

👇 **Hemen izlemeye başlamak için** butona tıkla."""

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

# ================== CALLBACKS ==================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == "open_mini_app":
        if not has_full_access(user_id):
            bot.answer_callback_query(call.id, "❌ Kanaldan veya gruptan çıkmışsın. Tekrar katılman gerekiyor.", show_alert=True)
            return

        bot.answer_callback_query(call.id)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎥 Mini Uygulamayı Aç", web_app=WebAppInfo(url=MINI_APP_URL)))

        # Butonlu mesajı gönder
        sent_msg = bot.send_message(
            call.message.chat.id, 
            "✅ Erişim onaylandı!\nAşağıdaki butona basarak uygulamayı açabilirsiniz:", 
            reply_markup=markup
        )

        # 40 saniye sonra mesajı otomatik sil
        time.sleep(40)
        try:
            bot.delete_message(call.message.chat.id, sent_msg.message_id)
        except:
            pass  # Zaten silinmişse hata verme

    elif call.data == "user_info":
        c.execute("SELECT is_vip FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        is_vip = result[0] if result else 0
        status = "✅ VIP Kullanıcı" if is_vip else "👤 Normal Kullanıcı"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"""👤 **Kullanıcı Bilgileriniz**

Durum: {status}
ID: `{user_id}`""", parse_mode='Markdown')

    # ================== ADMIN CALLBACKS ==================
    elif call.data.startswith("admin_") or call.data in ["stats", "export_users", "broadcast", "send_to_user", "banned_users"] or call.data.startswith("unban_") or call.data == "back_to_admin":
        if not is_admin(call.from_user.id):
            return

        if call.data == "stats":
            c.execute("SELECT COUNT(*) FROM users")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE is_vip=1")
            vip = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE is_banned=1")
            banned = c.fetchone()[0]
            text = f"""📊 **Bot İstatistikleri**

• Toplam Kullanıcı: `{total}`
• VIP Kullanıcı: `{vip}`
• Banlı Kullanıcı: `{banned}`"""
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Admin Menü", callback_data="back_to_admin"))
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

        elif call.data == "export_users":
            c.execute("SELECT user_id, username, first_name, is_vip, is_banned, join_date FROM users")
            users = c.fetchall()
            if not users:
                return bot.send_message(call.message.chat.id, "Henüz kullanıcı yok.")
            
            text = "UserID,Username,FirstName,VIP,Banned,JoinDate\n"
            for u in users:
                text += f"{u[0]},{u[1] or ''},{u[2] or ''},{u[3]},{u[4]},{u[5]}\n"
            
            with open("users_export.csv", "w", encoding="utf-8") as f:
                f.write(text)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Admin Menü", callback_data="back_to_admin"))
            bot.send_document(call.message.chat.id, open("users_export.csv", "rb"), caption="✅ Tüm kullanıcılar export edildi.", reply_markup=markup)

        elif call.data == "banned_users":
            c.execute("SELECT user_id, username, first_name FROM users WHERE is_banned=1")
            banned = c.fetchall()
            
            if not banned:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🔙 Admin Menü", callback_data="back_to_admin"))
                return bot.send_message(call.message.chat.id, "✅ Banlı kullanıcı bulunmuyor.", reply_markup=markup)
            
            text = "⛔ **Banlı Kullanıcılar**\n\n"
            markup = InlineKeyboardMarkup(row_width=1)
            
            for b in banned:
                text += f"• `{b[0]}` | @{b[1] or 'NoUsername'}\n"
                markup.add(InlineKeyboardButton(f"Unban: {b[0]}", callback_data=f"unban_{b[0]}"))
            
            markup.add(InlineKeyboardButton("🔙 Admin Menü", callback_data="back_to_admin"))
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

        elif call.data.startswith("unban_"):
            try:
                target_id = int(call.data.split("_")[1])
                c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (target_id,))
                conn.commit()
                bot.answer_callback_query(call.id, f"✅ {target_id} unban edildi.", show_alert=True)
            except:
                bot.answer_callback_query(call.id, "Hata!", show_alert=True)

        elif call.data == "back_to_admin":
            admin_panel(call.message)

        elif call.data == "broadcast":
            markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(KeyboardButton("📝 Sadece Metin"))
            markup.add(KeyboardButton("🖼 Fotoğraf + Metin"))
            markup.add(KeyboardButton("🎥 Video + Metin"))
            bot.send_message(call.message.chat.id, "📢 Duyuru türünü seçin:", reply_markup=markup)

        elif call.data == "send_to_user":
            bot.send_message(call.message.chat.id, "🔸 Mesaj göndermek istediğin kullanıcı ID'sini yaz:")
            bot.register_next_step_handler(call.message, process_user_id_for_message)

# ================== ADMIN PANEL ==================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ Bu komut sadece adminlere özeldir.")

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("📊 İstatistik", callback_data="stats"))
    markup.add(InlineKeyboardButton("👥 Tüm Üyeler", callback_data="admin_users_0"))
    markup.add(InlineKeyboardButton("⛔ Banlı Listesi", callback_data="banned_users"))
    markup.add(InlineKeyboardButton("📤 Export Kullanıcılar", callback_data="export_users"))
    markup.add(InlineKeyboardButton("✉️ Özel Mesaj", callback_data="send_to_user"))
    markup.add(InlineKeyboardButton("📢 Toplu Duyuru", callback_data="broadcast"))

    bot.send_message(message.chat.id, "🛠 **Admin Paneli**", reply_markup=markup)

# ================== DİĞER FONKSİYONLAR ==================
@bot.message_handler(func=lambda m: m.text in ["📝 Sadece Metin", "🖼 Fotoğraf + Metin", "🎥 Video + Metin"])
def broadcast_type_selected(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Şimdi duyuru içeriğini gönder (metin, fotoğraf veya video):")
    bot.register_next_step_handler(message, lambda m: send_broadcast(m, message.text))

def send_broadcast(message, broadcast_type):
    if not is_admin(message.from_user.id):
        return
    try:
        c.execute("SELECT user_id FROM users WHERE is_banned=0")
        users = c.fetchall()
        sent = 0
        for user in users:
            try:
                if broadcast_type == "📝 Sadece Metin":
                    bot.send_message(user[0], message.text)
                elif broadcast_type == "🖼 Fotoğraf + Metin" and message.photo:
                    bot.send_photo(user[0], message.photo[-1].file_id, caption=message.caption or "")
                elif broadcast_type == "🎥 Video + Metin" and message.video:
                    bot.send_video(user[0], message.video.file_id, caption=message.caption or "")
                sent += 1
            except:
                continue
        bot.send_message(message.chat.id, f"✅ Duyuru {sent} kullanıcıya gönderildi.")
    except:
        bot.send_message(message.chat.id, "❌ Duyuru gönderilirken hata oluştu.")

def process_user_id_for_message(message):
    try:
        target_id = int(message.text)
        bot.send_message(message.chat.id, f"✅ ID: `{target_id}`\nŞimdi göndermek istediğin mesajı yaz:", parse_mode='Markdown')
        bot.register_next_step_handler(message, lambda m: send_private_message(m, target_id))
    except:
        bot.send_message(message.chat.id, "❌ Geçersiz ID!")

def send_private_message(message, user_id):
    try:
        bot.forward_message(user_id, message.chat.id, message.id)
        bot.send_message(message.chat.id, "✅ Mesaj başarıyla gönderildi!")
    except:
        bot.send_message(message.chat.id, "❌ Mesaj gönderilemedi.")

# ================== BOT ÇALIŞTIR ==================
if __name__ == "__main__":
    print("🔥 Porno Bot Başarıyla Çalışıyor...")
    bot.infinity_polling()
