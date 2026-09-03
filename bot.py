import telebot
import requests

# ===== НАСТРОЙКИ =====
API_KEY = "sk-cduX9UbA3kV92Y0ecbbtL8TpoIRQZevma5bQZVVPWdVtv0Kx"
BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"
# ====================

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Бот работает! Отправь текст — я отвечу через ИИ.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        url = "https://api.chatanywhere.tech/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": message.text}]
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            bot.reply_to(message, reply[:4096])
        else:
            bot.reply_to(message, f"❌ Ошибка API: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Сбой: {str(e)[:200]}")

print("🚀 Бот с GPT запущен...")
bot.infinity_polling()
