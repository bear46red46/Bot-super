import telebot
from flask import Flask, request
import os

# =========================
# SOZLAMALAR
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "7316977124,6937418004"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Render Environment Variables ga qo‘shing.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

USERS_FILE = "users.txt"

# =========================
# USER SAQLASH
# =========================
def save_user(user_id):
    user_id = str(user_id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            f.write(user_id + "\n")
    else:
        with open(USERS_FILE, "r") as f:
            users = f.read().splitlines()
        if user_id not in users:
            with open(USERS_FILE, "a") as f:
                f.write(user_id + "\n")

def get_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return f.read().splitlines()

# =========================
# /start
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    save_user(user_id)

    if user_id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 Userlar soni", "📢 Reklama")

        bot.send_message(user_id, "👨‍💼 Admin panelga xush kelibsiz", reply_markup=markup)
    else:
        bot.send_message(
            user_id,
            "👋 Assalomu alaykum!\n\n"
            "🤖 Botimizga hush kelibsiz!\n\n"
            "📩 Adminga murojaatingizni yozing.\n"
            "Admin tez orada javob beradi."
        )

# =========================
# USER → ADMINGA
# =========================
@bot.message_handler(func=lambda message: message.from_user.id != ADMIN_ID)
def forward_to_admin(message):
    user = message.from_user
    save_user(user.id)

    username = f"@{user.username}" if user.username else "Yo‘q"

    text = f"""📩 Yangi murojaat

👤 Ism: {user.first_name}
🔗 Username: {username}
🆔 ID: {user.id}

💬 Xabar:
{message.text}
"""

    bot.send_message(ADMIN_ID, text)
    bot.send_message(user.id, "✅ Habaringiz adminga yuborildi.\n⏳ Javobni kuting.")

# =========================
# ADMIN REPLY
# =========================
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.reply_to_message)
def admin_reply(message):
    try:
        reply_text = message.reply_to_message.text
        user_id_line = [line for line in reply_text.split("\n") if "🆔 ID:" in line][0]
        user_id = int(user_id_line.replace("🆔 ID:", "").strip())

        bot.send_message(user_id, f"📨 Admin javobi:\n\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ Javob yuborildi.")

    except Exception as e:
        bot.send_message(ADMIN_ID, "❌ Xatolik! To‘g‘ri murojaatga reply qiling.")

# =========================
# USERLAR SONI
# =========================
@bot.message_handler(func=lambda message: message.text == "📊 Userlar soni")
def user_count(message):
    if message.from_user.id == ADMIN_ID:
        users = get_users()
        bot.send_message(ADMIN_ID, f"📊 Userlar soni: {len(users)}")

# =========================
# REKLAMA
# =========================
@bot.message_handler(func=lambda message: message.text == "📢 Reklama")
def ask_broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "📢 Reklama matnini yuboring:")
        bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    users = get_users()
    count = 0
    for user in users:
        try:
            bot.send_message(user, message.text)
            count += 1
        except:
            pass

    bot.send_message(ADMIN_ID, f"✅ Reklama {count} ta userga yuborildi.")

# =========================
# FLASK ROUTES
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
# WEBHOOK O‘RNATISH
# =========================
if __name__ == "__main__":
    bot.remove_webhook()

    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

    if not RENDER_URL:
        raise ValueError("RENDER_EXTERNAL_URL topilmadi!")

    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
