import os
import telebot

import os
import telebot

# Use environment variable for security
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("[ERROR] TELEGRAM_BOT_TOKEN environment variable not set.")
    exit(1)

bot = telebot.TeleBot(TOKEN)
print("--- Pro Guardian Bot Active ---")
print(f"[DEBUG] Listening on token: {TOKEN[:5]}...")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    print(f"[CHAT] Received command from chat_id: {message.chat.id}")
    bot.reply_to(message, "Guardian System Online. Analyzing BSC and Arbitrum networks.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(f"[CHAT] Received message: {message.text} from {message.chat.id}")
    bot.reply_to(message, "Message received. Monitoring active shadow testing cycles.")

bot.infinity_polling()
