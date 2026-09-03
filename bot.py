import telebot
import requests
import json
from datetime import date

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"
API_KEY_9ROUTER = "sk-9a01ae3cc4d291b1-vwry29-564841cc"
URL_9ROUTER = "https://9router-production-b249e.up.railway.app/v1/chat/completions"
# ====================

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ===== ДОСТУПНЫЕ МОДЕЛИ =====
MODELS = {
    "kr/claude-sonnet-4.5": {"name": "Claude Sonnet 4.5", "desc": "Универсальная, лучший баланс", "limit": 200},
    "kr/claude-haiku-4.5": {"name": "Claude Haiku 4.5", "desc": "Быстрая, лёгкая", "limit": 200},
    "kr/claude-sonnet-4.5-thinking": {"name": "Claude Sonnet 4.5 (Thinking)", "desc": "Глубокие рассуждения", "limit": 150},
    "kr/claude-haiku-4.5-thinking": {"name": "Claude Haiku 4.5 (Thinking)", "desc": "Быстрая с мышлением", "limit": 150},
    "kr/claude-sonnet-4.5-agentic": {"name": "Claude Sonnet 4.5 (Agentic)", "desc": "Выполнение действий", "limit": 150},
    "kr/claude-haiku-4.5-agentic": {"name": "Claude Haiku 4.5 (Agentic)", "desc": "Быстрая, агентная", "limit": 150},
    "kr/claude-sonnet-4.5-thinking-agentic": {"name": "Claude Sonnet 4.5 (Thinking+Agentic)", "desc": "Максимальная мощность", "limit": 100},
    "kr/claude-haiku-4.5-thinking-agentic": {"name": "Claude Haiku 4.5 (Thinking+Agentic)", "desc": "Быстрая, мощная", "limit": 100},
    "kr/qwen3-coder-next": {"name": "Qwen3 Coder", "desc": "Для кода и программирования", "limit": 200},
    "kr/deepseek-3.2": {"name": "DeepSeek 3.2", "desc": "Альтернативная, бюджетная", "limit": 200},
    "kr/glm-5": {"name": "GLM-5", "desc": "Китайская модель", "limit": 200},
}

user_models = {}
user_requests = {}

def get_user_model(user_id):
    return user_models.get(user_id, "kr/claude-sonnet-4.5")

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    model_id = get_user_model(message.chat.id)
    model_name = MODELS.get(model_id, {}).get("name", "Claude Sonnet 4.5")
    bot.reply_to(
        message,
        f"✅ Бот работает через 9Router!\n"
        f"Текущая модель: {model_name}\n"
        f"Лимит: {get_model_limit(model_id)} запросов/день\n\n"
        f"Команды:\n/model — выбрать модель\n/limits — остаток запросов\n/help — помощь\n/info — о боте"
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        "📖 Команды:\n"
        "/start — приветствие\n"
        "/model — выбрать модель ИИ\n"
        "/limits — остаток запросов\n"
        "/help — эта справка\n"
        "/info — информация о боте\n\n"
        "Просто напиши вопрос — я отвечу."
    )

@bot.message_handler(commands=['info'])
def send_info(message):
    bot.reply_to(
        message,
        "🤖 Бот работает через 9Router с доступом к 11 моделям:\n"
        "• Claude Sonnet 4.5 (универсальная)\n"
        "• Claude Haiku 4.5 (быстрая)\n"
        "• Thinking-версии (глубокие рассуждения)\n"
        "• Agentic-версии (выполнение действий)\n"
        "• Qwen3 Coder (для кода)\n"
        "• DeepSeek 3.2 и GLM-5 (альтернативные)\n\n"
        "Доступ 24/7. Все модели бесплатны."
    )

@bot.message_handler(commands=['limits'])
def show_limits(message):
    user_id = message.chat.id
    remaining = get_remaining_requests(user_id)
    model_id = get_user_model(user_id)
    model_name = MODELS.get(model_id, {}).get("name", "неизвестная модель")
    limit = get_model_limit(model_id)
    bot.reply_to(
        message,
        f"📊 *Остаток запросов на сегодня:*\n"
        f"Модель: {model_name}\n"
        f"Осталось: {remaining} из {limit}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['model'])
def show_models(message):
    user_id = message.chat.id
    current_model = get_user_model(user_id)
    current_name = MODELS.get(current_model, {}).get("name", "не выбрана")
    remaining = get_remaining_requests(user_id)

    text = f"🧠 *Выбери модель ИИ:*\n\n"
    text += f"📌 *Текущая модель:* {current_name}\n"
    text += f"📊 *Остаток запросов:* {remaining}\n\n"

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
        f"Остаток на сегодня: {remaining}",
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

        model_id = get_user_model(user_id)
        bot.send_chat_action(user_id, 'typing')

        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": message.text}],
            "stream": False
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY_9ROUTER}"
        }

        response = requests.post(URL_9ROUTER, headers=headers, json=payload, timeout=45)

        if response.status_code == 200:
            try:
                reply = response.json()["choices"][0]["message"]["content"]
                bot.reply_to(message, reply[:4096])
            except (KeyError, json.JSONDecodeError):
                bot.reply_to(message, f"❌ Ошибка: не удалось распарсить ответ от модели.")
        else:
            bot.reply_to(message, f"❌ Ошибка API: {response.status_code}\n{response.text[:300]}")

    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏳ Модель не отвечает. Попробуй ещё раз.")
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "❌ Не удалось подключиться к 9Router. Проверь, что сервис запущен.")
    except Exception as e:
        bot.reply_to(message, f"❌ Сбой: {str(e)[:200]}")

print("🚀 Бот на 9Router с выбором моделей запущен...")
bot.infinity_polling()
