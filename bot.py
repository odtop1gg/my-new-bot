import telebot
import requests
import json
from datetime import date
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"

# ===== 9ROUTER (KIRO) =====
KIRO_URL = "https://9router-production-b249e.up.railway.app/v1/chat/completions"
KIRO_API_KEY = "sk-9a01ae3cc4d291b1-vwry29-564841cc"

# ===== API.AIRFORCE =====
AIRFORCE_URL = "https://api.airforce/v1/chat/completions"
AIRFORCE_API_KEY = "sk-air-XCS2bXZgzsQeW8ITSY1SuXE1c5EOr10rNIppOYx2zN0T1LCf"

# ===== ПРЯМОЙ GEMINI =====
GEMINI_API_KEY = "AQ.Ab8RN6Lj_kjFfg0fpLcgM0ZDAS_rZPN-gAqZ-z-jz9fjyeAIzw"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ===== МОДЕЛИ =====
MODELS = {
    # ===== 9ROUTER (KIRO) =====
    "kr/claude-sonnet-4.5": {
        "name": "Claude Sonnet 4.5 (Kiro)",
        "desc": "Баланс скорости и качества",
        "provider": "kiro",
        "limit": 200
    },
    "kr/claude-haiku-4.5": {
        "name": "Claude Haiku 4.5 (Kiro)",
        "desc": "Быстрая и лёгкая",
        "provider": "kiro",
        "limit": 200
    },
    "kr/qwen3-coder-next": {
        "name": "Qwen3 Coder (Kiro)",
        "desc": "Для кода",
        "provider": "kiro",
        "limit": 200
    },
    "kr/deepseek-3.2": {
        "name": "DeepSeek 3.2 (Kiro)",
        "desc": "Альтернативная",
        "provider": "kiro",
        "limit": 200
    },
    "kr/glm-5": {
        "name": "GLM-5 (Kiro)",
        "desc": "Китайская",
        "provider": "kiro",
        "limit": 200
    },

    # ===== API.AIRFORCE =====
    "grok-4.1-fast-reasoning": {
        "name": "Grok 4.1 (xAI)",
        "desc": "Мощная логика, 2M контекста",
        "provider": "airforce",
        "limit": 200
    },
    "gemini-3.6-flash": {
        "name": "Gemini 3.6 Flash (Airforce)",
        "desc": "От Google, сбалансированная",
        "provider": "airforce",
        "limit": 200
    },
    "glm-5.3-flash": {
        "name": "GLM 5.3 Flash",
        "desc": "Огромный контекст (200K)",
        "provider": "airforce",
        "limit": 200
    },
    "gpt-oss-120b": {
        "name": "GPT-OSS 120B",
        "desc": "От OpenAI, открытая",
        "provider": "airforce",
        "limit": 200
    },

    # ===== ПРЯМОЙ GEMINI =====
    "gemini-3.6-flash-direct": {
        "name": "Gemini 3.6 Flash (прямой)",
        "desc": "От Google, прямой ключ",
        "provider": "gemini_direct",
        "model_id": "gemini-2.0-flash",
        "limit": 200
    },
    "gemini-3.5-flash-lite": {
        "name": "Gemini 3.5 Flash Lite",
        "desc": "Очень быстрая, дешёвая",
        "provider": "gemini_direct",
        "model_id": "gemini-2.5-flash-lite",
        "limit": 200
    },
}

user_models = {}
user_requests = {}
user_history = {}

def get_user_model(user_id):
    return user_models.get(user_id, "kr/claude-sonnet-4.5")

def set_user_model(user_id, model_id):
    user_models[user_id] = model_id

def get_model_info(model_id):
    return MODELS.get(model_id, {})

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

# ===== ФУНКЦИИ ОТПРАВКИ =====
def send_to_kiro(model_id, history):
    payload = {
        "model": model_id,
        "messages": history,
        "stream": False
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIRO_API_KEY}"
    }
    response = requests.post(KIRO_URL, headers=headers, json=payload, timeout=45)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Ошибка Kiro: {response.status_code}")

def send_to_airforce(model_id, history):
    payload = {
        "model": model_id,
        "messages": history,
        "stream": False
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIRFORCE_API_KEY}"
    }
    response = requests.post(AIRFORCE_URL, headers=headers, json=payload, timeout=45)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Ошибка Airforce: {response.status_code}")

def send_to_gemini_direct(model_id, history):
    # Собираем последние 3 сообщения пользователя
    user_messages = [msg["content"] for msg in history if msg["role"] == "user"]
    prompt = "\n".join(user_messages[-3:]) if user_messages else "Привет!"
    url = GEMINI_URL.format(model=model_id, key=GEMINI_API_KEY)
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=data, timeout=45)
    if response.status_code == 200:
        result = response.json()
        text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not text:
            raise Exception("Пустой ответ от Gemini")
        return text
    else:
        raise Exception(f"Ошибка Gemini: {response.status_code}")

def send_to_model(model_id, history):
    info = get_model_info(model_id)
    provider = info.get("provider")
    if provider == "kiro":
        return send_to_kiro(model_id, history)
    elif provider == "airforce":
        return send_to_airforce(model_id, history)
    elif provider == "gemini_direct":
        real_model = info.get("model_id", "gemini-2.0-flash")
        return send_to_gemini_direct(real_model, history)
    else:
        raise Exception(f"Неизвестный провайдер: {provider}")

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
    model_name = MODELS.get(model_id, {}).get("name", "Claude Sonnet 4.5")
    bot.send_message(
        message.chat.id,
        f"✅ Бот работает на 3 провайдерах!\n"
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
        "🤖 Бот работает на 3 провайдерах:\n"
        "• 9Router (Kiro) — Claude, Qwen, DeepSeek, GLM\n"
        "• API.airforce — Grok, Gemini, GPT-OSS, GLM\n"
        "• Прямой Gemini — от Google\n\n"
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

        reply = send_to_model(model_id, history)

        add_to_history(user_id, "assistant", reply)
        bot.reply_to(message, reply[:4096])

    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏳ Модель не отвечает. Попробуй ещё раз.")
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "❌ Не удалось подключиться к API.")
    except Exception as e:
        bot.reply_to(message, f"❌ Сбой: {str(e)[:200]}")

print("🚀 Бот на 3 провайдерах запущен...")
bot.infinity_polling()
