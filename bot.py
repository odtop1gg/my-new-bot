import telebot
import requests
import json
from datetime import date, datetime
from collections import Counter
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "8940791068:AAHQTMEEs2Ucc2o75Pp64GwhShF0lZM0H5I"
KIRO_URL = "https://9router-production-b249e.up.railway.app/v1/chat/completions"
KIRO_API_KEY = "sk-9a01ae3cc4d291b1-vwry29-564841cc"

ADMIN_USERNAME = "NeUstaI"  # Твой юзернейм

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ===== МОДЕЛИ =====
MODELS = {
    "kr/claude-sonnet-4.5": {"name": "Claude Sonnet 4.5", "desc": "Универсальная", "limit": 200},
    "kr/claude-haiku-4.5": {"name": "Claude Haiku 4.5", "desc": "Быстрая (резерв)", "limit": 200},
    "kr/deepseek-3.2": {"name": "DeepSeek 3.2", "desc": "Альтернатива (резерв)", "limit": 200},
}

user_models = {}
user_requests = {}
user_history = {}
allowed_users = set()  # храним юзернеймы

def is_admin(user):
    return user.username == ADMIN_USERNAME

def is_allowed(user):
    return user.username in allowed_users or is_admin(user)

def load_allowed():
    try:
        with open("allowed.txt", "r") as f:
            return set(line.strip().replace("@", "") for line in f if line.strip())
    except:
        return set()

def save_allowed():
    with open("allowed.txt", "w") as f:
        for username in allowed_users:
            f.write(f"{username}\n")

allowed_users = load_allowed()

# ===== ФУНКЦИИ (остальные без изменений) =====
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

def get_user_history(user_id):
    if user_id not in user_history:
        user_history[user_id] = []
    return user_history[user_id]

def add_to_history(user_id, role, content):
    history = get_user_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > 20:
        history.pop(0)

def send_to_kiro(model_id, history):
    payload = {"model": model_id, "messages": history, "stream": False}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {KIRO_API_KEY}"}
    response = requests.post(KIRO_URL, headers=headers, json=payload, timeout=45)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Kiro: {response.status_code}")

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📖 Помощь"), KeyboardButton("ℹ️ О боте"), KeyboardButton("🧠 Модель"), KeyboardButton("📊 Лимиты"))
    return markup

# ===== КОМАНДЫ АДМИНА =====
@bot.message_handler(commands=['adduser'])
def add_user(message):
    if not is_admin(message.from_user):
        bot.reply_to(message, "⛔ Нет прав.")
        return
    try:
        username = message.text.split()[1].replace("@", "")
        allowed_users.add(username)
        save_allowed()
        bot.reply_to(message, f"✅ Пользователь @{username} добавлен.")
    except:
        bot.reply_to(message, "❌ Используй: /adduser @username")

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if not is_admin(message.from_user):
        bot.reply_to(message, "⛔ Нет прав.")
        return
    try:
        username = message.text.split()[1].replace("@", "")
        allowed_users.discard(username)
        save_allowed()
        bot.reply_to(message, f"✅ Пользователь @{username} удалён.")
    except:
        bot.reply_to(message, "❌ Используй: /removeuser @username")

@bot.message_handler(commands=['listusers'])
def list_users(message):
    if not is_admin(message.from_user):
        bot.reply_to(message, "⛔ Нет прав.")
        return
    text = "📋 Разрешённые пользователи:\n" + "\n".join(f"@{u}" for u in allowed_users)
    bot.reply_to(message, text or "Список пуст")

# ===== ОСТАЛЬНЫЕ КОМАНДЫ (те же) =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_allowed(message.from_user):
        bot.reply_to(message, "⛔ Доступ запрещён. Обратитесь к @NeUstaI")
        return
    model_id = get_user_model(message.chat.id)
    model_name = MODELS.get(model_id, {}).get("name", "Claude Sonnet 4.5")
    bot.send_message(
        message.chat.id,
        f"✅ Бот на Claude + резерв\n"
        f"Текущая модель: {model_name}\n"
        f"Лимит: {get_model_limit(model_id)} запросов/день\n\n"
        f"Выбери действие на клавиатуре или напиши вопрос.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == "📖 Помощь")
def help_button(message):
    if not is_allowed(message.from_user): return
    bot.send_message(
        message.chat.id,
        "📖 Команды:\n/start — главное меню\n/model — выбрать модель\n/limits — остаток запросов\n/help — справка\n/info — о боте\n\nИли используй кнопки внизу.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == "ℹ️ О боте")
def info_button(message):
    if not is_allowed(message.from_user): return
    bot.send_message(
        message.chat.id,
        "🤖 Бот на Kiro (Claude + резерв).\nВсе модели бесплатны.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == "🧠 Модель")
def model_button(message):
    if not is_allowed(message.from_user): return
    show_models(message)

@bot.message_handler(func=lambda message: message.text == "📊 Лимиты")
def limits_button(message):
    if not is_allowed(message.from_user): return
    show_limits(message)

@bot.message_handler(commands=['limits'])
def show_limits(message):
    if not is_allowed(message.from_user): return
    user_id = message.chat.id
    remaining = get_remaining_requests(user_id)
    model_id = get_user_model(user_id)
    model_name = MODELS.get(model_id, {}).get("name", "неизвестная модель")
    limit = get_model_limit(model_id)
    bot.send_message(
        message.chat.id,
        f"📊 *Остаток запросов на сегодня:*\nМодель: {model_name}\nОсталось: {remaining} из {limit}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['model'])
def show_models(message):
    if not is_allowed(message.from_user): return
    user_id = message.chat.id
    current_model = get_user_model(user_id)
    current_name = MODELS.get(current_model, {}).get("name", "не выбрана")
    remaining = get_remaining_requests(user_id)

    text = f"🧠 *Выбери модель:*\n\n📌 *Текущая:* {current_name}\n📊 *Остаток:* {remaining}\n\n"
    markup = telebot.types.InlineKeyboardMarkup()
    for model_id, info in MODELS.items():
        btn_text = f"{info['name']} — {info['limit']} запр./день"
        btn = telebot.types.InlineKeyboardButton(btn_text, callback_data=f"model_{model_id}")
        markup.add(btn)

    text += "Нажми на кнопку, чтобы сменить модель."
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("model_"))
def set_model_callback(call):
    if not is_allowed(call.from_user):
        bot.answer_callback_query(call.id, "⛔ Доступ запрещён")
        return
    model_id = call.data.split("_", 1)[1]
    set_user_model(call.message.chat.id, model_id)
    model_name = MODELS.get(model_id, {}).get("name", "неизвестная модель")
    limit = get_model_limit(model_id)
    remaining = get_remaining_requests(call.message.chat.id)
    bot.answer_callback_query(call.id, f"✅ Модель изменена на {model_name}")
    bot.edit_message_text(
        f"✅ Модель изменена на **{model_name}**.\nЛимит: {limit} запросов/день.\nОстаток: {remaining}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not is_allowed(message.from_user):
        return

    try:
        user_id = message.chat.id
        if not can_send_message(user_id):
            bot.reply_to(message, "⚠️ Ты исчерпал дневной лимит.")
            return

        model_id = get_user_model(user_id)
        add_to_history(user_id, "user", message.text)
        history = get_user_history(user_id)

        reply = send_to_kiro(model_id, history)
        reply += "\n\n👨‍💻 Создатель: @NeUstaI"

        add_to_history(user_id, "assistant", reply)
        bot.reply_to(message, reply[:4096])

    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏳ Модель не отвечает. Попробуй ещё раз.")
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "❌ Не удалось подключиться к 9Router.")
    except Exception as e:
        bot.reply_to(message, f"❌ Сбой: {str(e)[:200]}")

print("🚀 Бот с доступом по юзернейму запущен...")
bot.infinity_polling()
