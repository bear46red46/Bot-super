import telebot
from flask import Flask, request
import sqlite3
import os

# =========================
# SOZLAMALAR
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ORIGINAL_ADMIN = int(os.getenv("ORIGINAL_ADMIN", "8500394413"))  # Original admin ID
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render URL

if not BOT_TOKEN or not RENDER_URL:
    raise ValueError("BOT_TOKEN yoki RENDER_EXTERNAL_URL topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    username TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    msg_id INTEGER,
    from_id INTEGER,
    to_id INTEGER
)
""")
conn.commit()

# =========================
# USER FUNCTIONS
# =========================
def add_user(user):
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, full_name, username, role)
        VALUES (?, ?, ?, ?)
    """, (
        user.id,
        user.first_name,
        user.username if user.username else "yo‘q",
        "user"
    ))
    conn.commit()

def get_role(user_id):
    if user_id == ORIGINAL_ADMIN:
        return "original"
    cursor.execute("SELECT role FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else "user"

def set_admin(user_id):
    cursor.execute("UPDATE users SET role='admin' WHERE user_id=?", (user_id,))
    conn.commit()

def remove_admin(user_id):
    cursor.execute("UPDATE users SET role='user' WHERE user_id=?", (user_id,))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT user_id, full_name, username FROM users")
    return cursor.fetchall()

def get_admins():
    cursor.execute("SELECT user_id, full_name, username FROM users WHERE role='admin'")
    return cursor.fetchall()

# =========================
# MENU FUNCTION
# =========================
from telebot import types

def main_menu(user_id):
    role = get_role(user_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if role == "original":
        markup.row("📩 Xabar yuborish","📢 Reklama")
        markup.row("📋 Adminlar ro‘yxati","📋 Foydalanuvchilar ro‘yxati")
        markup.row("➕ Admin qo‘shish", "➖ Admin o‘chirish")
        markup.row("📖 Yordam")
    elif role == "admin":
        markup.row("📩 Xabar yuborish")
        markup.row("📢 Reklama")
        markup.row("📋 Adminlar ro‘yxati")
        markup.row("📋 Foydalanuvchilar ro‘yxati")
        markup.row("📖 Yordam")
    else:
        markup.row("📩 Xabar yuborish")
        markup.row("👑 Adminga yozish")
        markup.row("📖 Yordam")
        markup.row("📓 Yoriqnoma")

    return markup

# =========================
# STATE STORAGE
# =========================
user_states = {}

# =========================
# /START HANDLER
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user)
    bot.send_message(
        message.chat.id,
        "👋 Assalomu aleykum\n\nBizning botimizga xush kelibsiz!",
        reply_markup=main_menu(message.from_user.id)
    )

# =========================
# UNIVERSAL XABAR YUBORISH
# =========================
@bot.message_handler(func=lambda m: m.text == "📩 Xabar yuborish")
def ask_user_id(message):
    msg = bot.send_message(message.chat.id, "🗨️ Foydalanuvchi ID raqamini yuboring:")
    bot.register_next_step_handler(msg, get_target_id)

def get_target_id(message):
    try:
        target_id = int(message.text)
        cursor.execute("SELECT user_id FROM users WHERE user_id=?", (target_id,))
        if not cursor.fetchone():
            bot.send_message(message.chat.id, "❌ Bu foydalanuvchi botda mavjud emas.")
            return

        user_states[message.from_user.id] = target_id
        msg = bot.send_message(message.chat.id, "🗨️ Xabar matnini yuboring:")
        bot.register_next_step_handler(msg, send_user_message)
    except:
        bot.send_message(message.chat.id, "❌ ID noto‘g‘ri.")

def send_user_message(message):
    sender_id = message.from_user.id
    if sender_id not in user_states:
        return

    target_id = user_states[sender_id]
    sender_name = message.from_user.first_name

    try:
        header = bot.send_message(
            target_id,
            f"📩 Yangi xabar\n\n👤 {sender_name}\nID: {sender_id}"
        )

        sent = bot.copy_message(target_id, message.chat.id, message.message_id)
        cursor.execute("INSERT INTO messages VALUES (?, ?, ?)", (sent.message_id, sender_id, target_id))
        conn.commit()

        bot.send_message(sender_id, "✅ Xabar yuborildi.")
    except:
        bot.send_message(sender_id, "❌ Xabar yuborishda xatolik.")

    del user_states[sender_id]

# =========================
# FLASK WEBHOOK ROUTES
# =========================
@app.route('/')
def home():
    return "Bot ishlayapti 🚀"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

# =========================
# RUN WEBHOOK
# =========================
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
