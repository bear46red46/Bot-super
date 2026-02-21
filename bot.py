import telebot
import os
import re
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

ADMINS = [7316977124, 6937418004, 8598165118]

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Assalomu alaykum!\n\nMurojaatingizni yozing."
    )

# Foydalanuvchi → Admin
@bot.message_handler(func=lambda m: m.chat.id not in ADMINS, content_types=['text'])
def to_admin(message):
    text = (
        f"📩 <b>Yangi murojaat!</b>\n\n"
        f"👤 {message.from_user.first_name}\n"
        f"🆔 <code>{message.from_user.id}</code>\n\n"
        f"{message.text}"
    )

    for admin_id in ADMINS:
        bot.send_message(admin_id, text)

    bot.send_message(message.chat.id, "✅ Yuborildi.")

# Admin → User
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def to_user(message):
    try:
        reply_text = message.reply_to_message.text or ""
        match = re.search(r"\d{5,}", reply_text)

        if not match:
            raise ValueError("ID topilmadi")

        target_id = int(match.group())

        bot.send_message(
            target_id,
            f"👨‍💻 <b>Admin javobi:</b>\n\n{message.text}"
        )

        bot.send_message(message.chat.id, "✅ Javob yuborildi.")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato: {e}")

# Webhook route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Health check (Render uchun)
@app.route("/")
def index():
    return "Bot ishlayapti 🚀"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(
        url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
