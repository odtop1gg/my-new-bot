import telebot
import requests
from datetime import date

API_KEY = "sk-cduX9UbA3kV92Y0ecbbtL8TpoIRQZevma5bQZVVPWdVtv0Kx"
BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ===== МОДЕЛИ И ИХ ЛИМИТЫ (из скриншотов) =====
MODELS = {
    # Топовые GPT (5 запросов в день)
    "gpt-5": {"name": "GPT-5", "limit": 5},
    "gpt-5.2": {"name": "GPT-5.2", "limit": 5},
    "gpt-4.1": {"name": "GPT-4.1", "limit": 5},
    "gpt-5.4": {"name": "GPT-5.4", "limit": 5},
    "gpt-4o": {"name": "GPT-4o", "limit": 5},
    "gpt-5.5": {"name": "GPT-5.5", "limit": 5},
    "gpt-5.1": {"name": "GPT-5.1", "limit": 5},
    "gpt-5.6-sol": {"name": "GPT-5.6-sol", "limit": 5},
    "gpt-5.6-terra": {"name": "GPT-5.6-terra", "limit": 5},
    # Мини-модели (100 запросов в день)
    "gpt-5.4-mini": {"name": "GPT-5.4-mini", "limit": 100},
    "gpt-4.1-mini": {"name": "GPT-4.1-mini", "limit": 100},
    "gpt-4o-mini": {"name": "GPT-4o-mini", "limit": 100},
    "gpt-5-mini": {"name": "GPT-5-mini", "limit": 100},
    "gpt-4.1-nano": {"name": "GPT-4.1-nano", "limit": 100},
    "gpt-5.4-nano": {"name": "GPT-5.4-nano", "limit": 100},
    "gpt-5-nano": {"name": "GPT-5-nano", "limit": 100},
    "gpt-5.6-luna": {"name": "GPT-5.6-luna", "limit": 100},
    # Дополнительно
    "gpt-3.5-turbo": {"name": "GPT-3.5-turbo", "limit": 200},
    # DeepSeek
    "deepseek-v3.2": {"name": "DeepSeek V3.2", "limit": 30},
    "deepseek-v3.2-thinking": {"name": "DeepSeek V3.2-thinking", "limit": 30},
    "deepseek-v4-pro": {"name": "DeepSeek V4 Pro", "limit": 30},
    "deepseek-chat": {"name": "DeepSeek Chat", "limit": 30},
    "deepseek-v4-flash": {"name": "DeepSeek V4 Flash", "limit": 80},
}

user_models = {}
user_requests = {}

def get_user_model(user_id):
    return user_models.get(user_id, "gpt-4o-mini")

def set_user_model(user_id, model_id):
    user_models[user_id] = model_id

def get_model_limit(user_id):
    model_id = get_user_model(user_id)
    if model_id in MODELS:
        return MODELS[model_id]["limit"]
    return 20

def can_send_message(user_id):
    today = date.today()
    if user_id not in user_requests:
        user_requests[user_id] = {"date": today, "count": 0}
    if user_requests[user_id]["date"] != today:
        user_requests[user_id] = {"date": today, "count": 0}
    limit = get_model_limit(user_id)
    if user_requests[user_id]["count"] >= limit:
        return False
    user_requests[user_id]["count"] += 1
    return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Бот работает! Отправь текст — я отвечу через ИИ.\nДля выбора модели нажми /model")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "📖 Команды:\n/start — приветствие\n/help — помощь\n/info — о боте\n/model — выбрать модель")

@bot.message_handler(commands=['info'])
def send_info(message):
    bot.reply_to(message, "🤖 Бот работает на 20+ моделях GPT и DeepSeek. Доступен 24/7.")

@bot.message_handler(commands=['model'])
def show_models(message):
    text = "🧠 *Выбери модель ИИ (лимит запросов в сутки):*\n\n"
    markup = telebot.types.InlineKeyboardMarkup()
    
    # Группировка по категориям для удобства
    categories = [
        ("Топовые GPT (5/день)", ["gpt-5", "gpt-5.2", "gpt-4.1", "gpt-5.4", "gpt-4o", "gpt-5.5", "gpt-5.1", "gpt-5.6-sol", "gpt-5.6-terra"]),
        ("Мини-модели (100/день)", ["gpt-5.4-mini", "gpt-4.1-mini", "gpt-4o-mini", "gpt-5-mini", "gpt-4.1-nano", "gpt-5.4-nano", "gpt-5-nano", "gpt-5.6-luna"]),
        ("Дополнительные", ["gpt-3.5-turbo"]),
        ("DeepSeek (30-80/день)", ["deepseek-v3.2", "deepseek-v3.2-thinking", "deepseek-v4-pro", "deepseek-chat", "deepseek-v4-flash"])
    ]
    
    for cat_name, model_ids in categories:
        text += f"*{cat_name}:*\n"
        for mid in model_ids:
            model = MODELS[mid]
            text += f"• {model['name']} — {model['limit']} запр./день\n"
            btn = telebot.types.InlineKeyboardButton(
                f"{model['name']} ({model['limit']})",
                callback_data=f"model_{mid}"
            )
            markup.add(btn)
        text += "\n"
    
    current_model = get_user_model(message.chat.id)
    current_name = MODELS.get(current_model, {}).get("name", "не выбрана")
    text += f"📌 *Текущая модель:* {current_name}\n\nНажми на кнопку, чтобы сменить модель."
    
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("model_"))
def set_model_callback(call):
    model_id = call.data.split("_")[1]
    set_user_model(call.message.chat.id, model_id)
    model_name = MODELS[model_id]["name"]
    limit = MODELS[model_id]["limit"]
    bot.answer_callback_query(call.id, f"✅ Модель изменена на {model_name}")
    bot.edit_message_text(
        f"✅ Модель изменена на **{model_name}**.\nЛимит: {limit} запросов в день.",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_id = message.chat.id

        if not can_send_message(user_id):
            bot.reply_to(message, "⚠️ Ты исчерпал дневной лимит запросов для этой модели.")
            return

        model = get_user_model(user_id)
        bot.send_chat_action(user_id, 'typing')
        
        url = "https://api.chatanywhere.tech/v1/chat/completions"
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {"model": model, "messages": [{"role": "user", "content": message.text}]}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            bot.reply_to(message, reply[:4096])
        else:
            bot.reply_to(message, f"❌ Ошибка API: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Сбой: {str(e)[:200]}")

print("🚀 Бот с расширенным функционалом запущен...")
bot.infinity_polling()
