import telebot
import requests
import json

BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Бот работает через 9Router + Claude Sonnet 4.5!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        url = "https://9router-production-b249e.up.railway.app/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-9a01ae3cc4d291b1-vwry29-564841cc"
        }
        data = {
            "model": "kr/claude-sonnet-4.5",
            "messages": [{"role": "user", "content": message.text}]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        # ===== ДИАГНОСТИКА =====
        # Если статус не 200 — показываем полный ответ
        if response.status_code != 200:
            bot.reply_to(message, f"❌ Статус: {response.status_code}\nОтвет сервера: {response.text[:500]}")
            return
        
        # Пытаемся распарсить JSON
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            bot.reply_to(message, f"❌ Ошибка: сервер вернул не JSON. Текст:\n{response.text[:500]}")
            return
        # =========================
        
        reply = response_json["choices"][0]["message"]["content"]
        bot.reply_to(message, reply[:4096])
        
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "❌ Не удалось подключиться к 9Router. Проверь, что сервис запущен.")
    except Exception as e:
        bot.reply_to(message, f"❌ Сбой: {str(e)[:200]}")

print("🚀 Бот на 9Router запущен...")
bot.infinity_polling()
