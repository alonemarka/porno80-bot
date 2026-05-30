import telebot
import sqlite3
import time
import threading
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from datetime import datetime

# ================== AYARLAR ==================
TOKEN = os.getenv("TOKEN") or "8742453459:AAF5uZYvU7JcADdSDyTm7hbc2tZQnfc5oPo"
MINI_APP_URL = "https://aloneai.gt.tc/"
CHANNEL_USERNAME = "@alonetools"
GROUP_USERNAME = "@atattv44vizyon"
ADMIN_IDS = [8773299135, 8973632679, 8230461239, 6318435017]

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
    if not GROUP_USERNAME:
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

# ================== 40 SANİYE SONRA SİLME ==================
def delete_after_delay(chat_id, message_id, delay=40):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

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
    markup.add(InlineKeyboardButton("🎥 Yapay Zeka Kullan", callback_data="open_mini_app"))
    markup.add(InlineKeyboardButton("👤 Bilgilerim", callback_data="user_info"))

    text = f"""🔥 **ALONE Aİ Dünyasına Hoş Geldiniz!** 🔥
Merhaba {first_name}!
✅ Kanala ve gruba katıldığın için teşekkürler.
👇 **Hemen kullanmaya başlamak için** butona tıkla."""

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

# ================== CALLBACK HANDLER ==================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    # ================== NORMAL KULLANICI ==================
    if call.data == "open_mini_app":
        if not has_full_access(user_id):
            bot.answer_callback_query(call.id, "❌ Kanaldan veya gruptan çıkmışsın. Tekrar katılman gerekiyor.", show_alert=True)
            return

        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎥 Mini Uygulamayı Aç", web_app=WebAppInfo(url=MINI_APP_URL)))

        sent_msg = bot.send_message(
            call.message.chat.id,
            "✅ Erişim onaylandı!\nAşağıdaki butona basarak uygulamayı açabilirsiniz:",
            reply_markup=markup
        )
        threading.Thread(target=delete_after_delay, args=(call.message.chat.id, sent_msg.message_id, 40), daemon=True).start()

    elif call.data == "user_info":
        c.execute("SELECT is_vip FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        is_vip = result[0] if result else 0
        status = "✅ VIP Kullanıcı" if is_vip else "👤 Normal Kullanıcı"

        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"""👤 **Kullanıcı Bilgileriniz**
Durum: {status}
ID: `{user_id}`""", parse_mode='Markdown')

    # ================== ADMIN PANEL ==================
    elif call.data in ["stats", "export_users", "broadcast", "send_to_user", "banned_users", "back_to_admin"] or call.data.startswith("admin_users_") or call.data.startswith("unban_"):
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

        elif call.data.startswith("admin_users_"):
            page = int(call.data.split("_")[2])
            per_page = 15
            offset = page * per_page

            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]

            c.execute("""SELECT user_id, username, first_name, is_vip, is_banned 
                        FROM users LIMIT ? OFFSET ?""", (per_page, offset))
            users = c.fetchall()

            text = f"""👥 **Tüm Kullanıcılar — Sayfa {page + 1}**
Toplam: {total_users}\n\n"""

            for u in users:
                username = f"@{u[1]}" if u[1] else "NoUsername"
                vip = "✅ VIP" if u[3] else ""
                ban = "⛔ BANLI" if u[4] else ""
                text += f"`{u[0]}` | {username} | {vip} {ban}\n"

            markup = InlineKeyboardMarkup(row_width=2)
            if page > 0:
                markup.add(InlineKeyboardButton("⬅️ Önceki", callback_data=f"admin_users_{page-1}"))
            if len(users) == per_page:
                markup.add(InlineKeyboardButton("Sonraki ➡️", callback_data=f"admin_users_{page+1}"))

            markup.add(InlineKeyboardButton("🔙 Admin Menü", callback_data="back_to_admin"))

            bot.edit_message_text(text, call.message.chat.id, call.message.id, reply_markup=markup, parse_mode='Markdown')

        elif call.data == "broadcast":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id, "📢 **Toplu Duyuru**\n\nGöndermek istediğiniz mesajı yazın (her tür mesaj desteklenir):")
            bot.register_next_step_handler(msg, process_broadcast)

        elif call.data == "send_to_user":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id, "👤 **Özel Mesaj**\n\nKullanıcının ID'sini gönder:")
            bot.register_next_step_handler(msg, process_send_to_user_id)

        elif call.data == "banned_users":
            c.execute("SELECT user_id, username, first_name FROM users WHERE is_banned=1")
            banned = c.fetchall()
            text = "⛔ **Banlı Kullanıcılar**\n\n"
            if not banned:
                text += "Banlı kullanıcı bulunmuyor."
            else:
                for u in banned:
                    text += f"`{u[0]}` | @{u[1] or 'NoUsername'} | {u[2]}\n"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Admin Menü", callback_data="back_to_admin"))
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

        elif call.data == "back_to_admin":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(InlineKeyboardButton("📊 İstatistik", callback_data="stats"))
            markup.add(InlineKeyboardButton("👥 Tüm Üyeler", callback_data="admin_users_0"))
            markup.add(InlineKeyboardButton("⛔ Banlı Listesi", callback_data="banned_users"))
            markup.add(InlineKeyboardButton("📤 Export Kullanıcılar", callback_data="export_users"))
            markup.add(InlineKeyboardButton("✉️ Özel Mesaj", callback_data="send_to_user"))
            markup.add(InlineKeyboardButton("📢 Toplu Duyuru", callback_data="broadcast"))
            bot.edit_message_text("🛠 **Admin Paneli**", call.message.chat.id, call.message.id, reply_markup=markup)

# ================== TOPLU DUYURU İŞLEME ==================
def process_broadcast(message):
    if not is_admin(message.from_user.id):
        return
    try:
        count = 0
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()
        
        for user in users:
            try:
                bot.copy_message(user[0], message.chat.id, message.message_id)
                count += 1
                time.sleep(0.05)  # Flood engeli
            except:
                continue
                
        bot.send_message(message.chat.id, f"✅ **Toplu duyuru başarıyla gönderildi!**\n\nToplam ulaşılan kullanıcı: `{count}`")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Hata oluştu: {str(e)}")

# ================== ÖZEL MESAJ İŞLEME ==================
def process_send_to_user_id(message):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
        msg = bot.send_message(message.chat.id, f"✅ ID alındı: `{target_id}`\n\nŞimdi göndermek istediğiniz mesajı yazın:")
        bot.register_next_step_handler(msg, lambda m: process_send_to_user_message(m, target_id))
    except:
        bot.send_message(message.chat.id, "❌ Geçersiz ID!")

def process_send_to_user_message(message, target_id):
    if not is_admin(message.from_user.id):
        return
    try:
        bot.copy_message(target_id, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, f"✅ Mesaj `{target_id}` ID'li kullanıcıya gönderildi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Mesaj gönderilemedi: {str(e)}")

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

# ================== BOT ÇALIŞTIR ==================
if __name__ == "__main__":
    print("🔥 ALONE AI Bot Başarıyla Çalışıyor...")
    bot.infinity_polling()
