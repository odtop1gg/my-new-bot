import telebot
import requests
import json
from datetime import date
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"

# ===== OPENROUTER =====
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ===== МОДЕЛИ OpenRouter (бесплатные) =====
MODELS = {
    "openai/gpt-4o-mini": {
        "name": "GPT-4o-mini",
        "desc": "Быстрая и дешёвая",
        "limit": 200
    },
    "openai/gpt-4o": {
        "name": "GPT-4o",
        "desc": "Мультимодальная",
        "limit": 200
    },
    "anthropic/claude-3.5-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "desc": "Универсальная",
        "limit": 200
    },
    "anthropic/claude-3-haiku": {
        "name": "Claude 3 Haiku",
        "desc": "Быстрая и лёгкая",
        "limit": 200
    },
    "google/gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "desc": "От Google",
        "limit": 200
    },
    "google/gemini-2.5-flash-lite": {
        "name": "Gemini 2.5 Flash Lite",
        "desc": "Очень быстрая",
        "limit": 200
    },
    "deepseek/deepseek-chat": {
        "name": "DeepSeek Chat",
        "desc": "Альтернативная",
        "limit": 200
    },
    "meta-llama/llama-3.3-70b-instruct:free": {
        "name": "Llama 3.3 70B",
        "desc": "От Meta, мощная",
        "limit": 200
    },
    "mistralai/mistral-7b-instruct:free": {
        "name": "Mistral 7B",
        "desc": "Открытая",
        "limit": 200
    },
}

user_models = {}
user_requests = {}
user_history = {}

def get_user_model(user_id):
    return user_models.get(user_id, "openai/gpt-4o-mini")

def set_user_model(user_id, model_id):
    user_models[user_id] = model_id

def get_model_limit(model_id):
    return MODELS.get(model_id, {}).get("limit", 100)

def can_send_message(user_id):
    today = date.today()
    model_id = get_user_model(user_id)
    limit = get_model_limit(model_id)
    if user_id not in user_requests:
        user_requests[user_id] = {"date": today, "count": 0}
    if user_requests[user_id]["date"] != today:
        user_requests[user_id] = {"date": today, "count": 0}
    if user_requests[user_id]["count"] >= limit:
        return False
    user_requests[user_id]["count"] += 1
    return True

def get_remaining_requests(user_id):
    today = date.today()
    model_id = get_user_model(user_id)
    limit = get_model_limit(model_id)
    if user_id not in user_requests or user_requests[user_id]["date"] != today:
        return limit
    used = user_requests[user_id]["count"]
    return max(0, limit - used)

def get_user_history(user_id):
    if user_id not in user_history:
        user_history[user_id] = []
    return user_history[user_id]

def add_to_history(user_id, role, content):
    history = get_user_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > 20:
        history.pop(0)

# ===== ОТПРАВКА В OPENROUTER =====
def send_to_openrouter(model_id, history):
    payload = {
        "model": model_id,
        "messages": history,
        "stream": False
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=45)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Ошибка OpenRouter: {response.status_code}")

# ===== КЛАВИАТУРА =====
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("📖 Помощь"),
        KeyboardButton("ℹ️ О боте"),
        KeyboardButton("🧠 Модель"),
        KeyboardButton("📊 Лимиты")
    )
    return markup

# ===== КОМАНДЫ =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    model_id = get_user_model(message.chat.id)
    model_name = MODELS.get(model_id, {}).get("name", "GPT-4o-mini")
    bot.send_message(
        message.chat.id,
        f"✅ Бот работает через OpenRouter!\n"
        f"Текущая модель: {model_name}\n"
        f"Лимит: {get_model_limit(model_id)} запросов/день\n\n"
        f"Выбери действие на клавиатуре или напиши вопрос.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == "📖 Помощь")
def help_button(message):
    send_help(message)

@bot.message_handler(func=lambda message: message.text == "ℹ️ О боте")
def info_button(message):
    send_info(message)

@bot.message_handler(func=lambda message: message.text == "🧠 Модель")
def model_button(message):
    show_models(message)

@bot.message_handler(func=lambda message: message.text == "📊 Лимиты")
def limits_button(message):
    show_limits(message)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(
        message.chat.id,
        "📖 Команды:\n"
        "/start — главное меню\n"
        "/model — выбрать модель\n"
        "/limits — остаток запросов\n"
        "/help — справка\n"
        "/info — о боте\n\n"
        "Или используй кнопки внизу.",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['info'])
def send_info(message):
    bot.send_message(
        message.chat.id,
        "🤖 Бот работает через OpenRouter.\n"
        "Доступны модели: GPT-4, Claude, Gemini, DeepSeek, Llama, Mistral.\n\n"
        "Все модели бесплатны.",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['limits'])
def show_limits(message):
    user_id = message.chat.id
    remaining = get_remaining_requests(user_id)
    model_id = get_user_model(user_id)
    model_name = MODELS.get(model_id, {}).get("name", "неизвестная модель")
    limit = get_model_limit(model_id)
    bot.send_message(
        message.chat.id,
        f"📊 *Остаток запросов на сегодня:*\n"
        f"Модель: {model_name}\n"
        f"Осталось: {remaining} из {limit}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['model'])
def show_models(message):
    user_id = message.chat.id
    current_model = get_user_model(user_id)
    current_name = MODELS.get(current_model, {}).get("name", "не выбрана")
    remaining = get_remaining_requests(user_id)

    text = f"🧠 *Выбери модель:*\n\n"
    text += f"📌 *Текущая:* {current_name}\n"
    text += f"📊 *Остаток:* {remaining}\n\n"

    markup = telebot.types.InlineKeyboardMarkup()
    for model_id, info in MODELS.items():
        btn_text = f"{info['name']} — {info['limit']} запр./день"
        btn = telebot.types.InlineKeyboardButton(btn_text, callback_data=f"model_{model_id}")
        markup.add(btn)

    text += "Нажми на кнопку, чтобы сменить модель."
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("model_"))
def set_model_callback(call):
    model_id = call.data.split("_", 1)[1]
    set_user_model(call.message.chat.id, model_id)
    model_name = MODELS.get(model_id, {}).get("name", "неизвестная модель")
    limit = get_model_limit(model_id)
    remaining = get_remaining_requests(call.message.chat.id)
    bot.answer_callback_query(call.id, f"✅ Модель изменена на {model_name}")
    bot.edit_message_text(
        f"✅ Модель изменена на **{model_name}**.\n"
        f"Лимит: {limit} запросов/день.\n"
        f"Остаток: {remaining}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# ===== ОСНОВНОЙ ОБРАБОТЧИК =====
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_id = message.chat.id

        if not can_send_message(user_id):
            bot.reply_to(message, "⚠️ Ты исчерпал дневной лимит.")
            return

        model_id = get_user_model(user_id)
        add_to_history(user_id, "user", message.text)
        history = get_user_history(user_id)

        reply = send_to_openrouter(model_id, history)

        add_to_history(user_id, "assistant", reply)
        bot.reply_to(message, reply[:4096])

    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏳ Модель не отвечает. Попробуй ещё раз.")
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "❌ Не удалось подключиться к OpenRouter.")
    except Exception as e:
        bot.reply_to(message, f"❌ Сбой: {str(e)[:200]}")

print("🚀 Бот на OpenRouter запущен...")
bot.infinity_polling()
