import os
import telebot
from flask import Flask, request

TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# /start komandasi
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Stars assalomu alaykum hush kelibsiz ⭐")

# Webhook route (Telegram shu yerga POST yuboradi)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Oddiy tekshiruv route
@app.route("/")
def home():
    return "Bot ishlayapti ✅", 200


# 🔥 MUHIM: gunicorn ishlaganda webhook o‘rnatiladi
bot.remove_webhook()
bot.set_webhook(
    url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
)
