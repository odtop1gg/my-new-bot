import telebot

BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Бот работает! Команда /start получена.")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"Ты сказал: {message.text}")

print("🚀 Бот запущен...")
bot.infinity_polling()