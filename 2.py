import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.exceptions import ChatNotFound
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

# =======================
# Конфигурация
# =======================
API_TOKEN = '7572193789:AAFojoL6qFz9fgCSsa1UW0veamzCi4lRHIY'
CHANNEL_USERNAME = '@mebizzy'  # Username канала без пробелов

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# =======================
# Подключение к базам данных
# =======================
referrals_db = "referrals.db"  # База данных рефералов
players_db = "players.db"  # База данных игроков

# Создание таблицы для players.db, если её нет
conn = sqlite3.connect(players_db)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS players (chat_id INTEGER PRIMARY KEY, player_id INTEGER)")
conn.commit()
conn.close()

# =======================
# Постоянная клавиатура
# =======================
def main_menu():
    """Возвращает главную клавиатуру с кнопкой 'Получить сигнал'."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📡 Получить сигнал"))
    return keyboard

# =======================
# Генерация сигнала
# =======================
def generate_signal():
    """Генерирует случайный сигнал из квадратов и звездочек, при этом звездочек будет меньше."""
    grid = []
    for _ in range(5):
        row = [random.choices(['🟦', '⭐️'], weights=[0.8, 0.2])[0] for _ in range(5)]
        grid.append(''.join(row))
    return '\n'.join(grid)

# =======================
# Проверка подписки на канал
# =======================
async def check_subscription(user_id):
    """Проверяет, подписан ли пользователь на канал."""
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except ChatNotFound:
        return False

# =======================
# Проверка наличия ID в referrals.db
# =======================
def is_referral_id(player_id):
    """Проверяет, существует ли player_id в базе referrals.db."""
    conn = sqlite3.connect(referrals_db)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM referrals WHERE user_id = ?", (player_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# =======================
# Добавление записи в players.db
# =======================
def add_to_players(chat_id, player_id):
    """Добавляет chat_id и player_id в базу данных players.db."""
    conn = sqlite3.connect(players_db)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO players (chat_id, player_id) VALUES (?, ?)", (chat_id, player_id))
    conn.commit()
    conn.close()

# =======================
# Проверка подписки с любым взаимодействием
# =======================
async def ensure_subscription(user_id, message: types.Message):
    """Проверяет подписку пользователя и, если он не подписан, требует подписку."""
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Подписаться", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
            InlineKeyboardButton("✅ Подписался", callback_data="check_subscription")
        )
        await message.answer("🤖 Вы не подписаны на канал! Пожалуйста, подпишитесь, чтобы продолжить.", reply_markup=keyboard)
        return False
    return True

# =======================
# Обработка команды /start
# =======================
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """Обрабатывает команду /start."""
    user_id = message.from_user.id

    # Проверка подписки
    if not await ensure_subscription(user_id, message):
        return

    # Проверка, есть ли пользователь уже в базе players.db
    conn = sqlite3.connect(players_db)
    cursor = conn.cursor()
    cursor.execute("SELECT player_id FROM players WHERE chat_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        await message.answer("✅ Ваш ID уже зарегистрирован. Нажмите на кнопку '📡 Получить сигнал' ниже, чтобы получить сигнал:", reply_markup=main_menu())
    else:
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("ℹ️ Где найти ID игрока?", url="https://telegra.ph/Gde-najti-ajdi-na-1win-12-17")
        )
        await message.answer("🤖 Пожалуйста, введите ваш ID игрока:", reply_markup=keyboard)

# =======================
# Обработка ввода ID игрока
# =======================
@dp.message_handler(lambda message: not message.text.startswith("📡"))
async def handle_player_id(message: types.Message):
    """Обрабатывает ввод ID игрока."""
    user_id = message.from_user.id

    # Проверка подписки
    if not await ensure_subscription(user_id, message):
        return

    try:
        player_id = int(message.text.strip())  # Преобразуем введённый текст в число

        # Проверяем, есть ли ID в базе referrals.db
        if is_referral_id(player_id):
            # Добавляем пользователя в players.db
            add_to_players(user_id, player_id)
            await message.answer("✅ Ваш ID успешно зарегистрирован. Нажмите на кнопку '📡 Получить сигнал' ниже, чтобы получить сигнал:", reply_markup=main_menu())
        else:
            await message.answer("⛔ Ваш ID не найден в базе. Проверьте правильность ввода.")

    except ValueError:
        await message.answer("⛔ Пожалуйста, введите корректный числовой ID.")

# =======================
# Обработка команды '📡 Получить сигнал'
# =======================
@dp.message_handler(lambda message: message.text == "📡 Получить сигнал")
async def send_signal_command(message: types.Message):
    """Обрабатывает команду 'Получить сигнал'."""
    user_id = message.from_user.id

    # Проверка подписки
    if not await ensure_subscription(user_id, message):
        return

    # Отсчет перед генерацией сигнала
    for i in range(10, 0, -1):
        await message.answer(f"⏳ Получение сигнала... {i} секунд")
        await asyncio.sleep(1)

    # Генерация и отправка сигнала
    signal = generate_signal()
    await message.answer(f"🤖 Сигнал:\n{signal}", reply_markup=main_menu())

# =======================
# Обработка проверки подписки
# =======================
@dp.callback_query_handler(lambda c: c.data == 'check_subscription')
async def verify_subscription(callback_query: types.CallbackQuery):
    """Обрабатывает проверку подписки."""
    is_subscribed = await check_subscription(callback_query.from_user.id)
    if is_subscribed:
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("ℹ️ Где найти ID игрока?", url="https://telegra.ph/Gde-najti-ajdi-na-1win-12-17")
        )
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="🤖 Пожалуйста, введите ваш ID игрока:",
            reply_markup=keyboard
        )
    else:
        await callback_query.answer("Вы не подписались на канал!", show_alert=True)

# =======================
# Запуск бота
# =======================
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
