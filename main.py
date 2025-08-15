import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# === НАСТРОЙКИ ===
TOKEN = "8481984389:AAHX9_fXrgemHmPeHNuX7pd2xJ1ooDkYgp4"
IMAGE_URL = "https://imgur.com/a/A8aIr3k"  # плейсхолдер
WELCOME_TEXT = (
    "Добро пожаловать в GiftKeeperOTC – надежный P2P-гарант\n\n"
    "💼 Покупайте и продавайте всё, что угодно – безопасно!\n"
    "От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
    "🔹 Удобное управление кошельками\n"
    "🔹 Реферальная система\n\n"
    "Выберите нужный раздел ниже:"
)

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)

# === БАЗА ДАННЫХ ===
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ton_wallet TEXT,
    bank_card TEXT
)
""")
conn.commit()

# === КНОПКИ ===
main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📥 Управление Реквизитами", callback_data="manage_requisites")],
    [InlineKeyboardButton(text="📄 Создать сделку", callback_data="create_deal")],
    [InlineKeyboardButton(text="🧷 Реферальная ссылка", callback_data="ref_link")],
    [InlineKeyboardButton(text="📞 Тех. Поддержка", callback_data="support")]
])

manage_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌑 Добавить/изменить TON-кошелек", callback_data="edit_ton")],
    [InlineKeyboardButton(text="💳 Добавить/изменить карту", callback_data="edit_card")],
    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
])

back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
])

# === БОТ ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.workflow_data = {}  # хранение временного состояния пользователей

# === КОМАНДА /start ===
@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer_photo(
        photo=IMAGE_URL,
        caption=WELCOME_TEXT,
        reply_markup=main_keyboard
    )

# === УПРАВЛЕНИЕ РЕКВИЗИТАМИ ===
@dp.callback_query(F.data == "manage_requisites")
async def manage_requisites(callback: types.CallbackQuery):
    text = (
        "📥 Управление реквизитами\n\n"
        "Используйте кнопки ниже, чтобы добавить/изменить реквизиты\n"
        "👇"
    )
    await callback.message.edit_caption(caption=text, reply_markup=manage_keyboard)

# === РЕДАКТИРОВАНИЕ TON-КОШЕЛЬКА ===
@dp.callback_query(F.data == "edit_ton")
async def edit_ton(callback: types.CallbackQuery):
    cursor.execute("SELECT ton_wallet FROM users WHERE user_id = ?", (callback.from_user.id,))
    result = cursor.fetchone()
    current_wallet = result[0] if result and result[0] else "не задан"
    text = (
        f"💼 Ваш текущий TON-кошелек: {current_wallet}\n\n"
        "Отправьте новый адрес кошелька для изменения или нажмите кнопку ниже для возврата в меню."
    )
    await callback.message.edit_caption(caption=text, reply_markup=back_keyboard)
    await bot.send_message(callback.from_user.id, "Введите новый TON-кошелек:")
    dp.workflow_data[str(callback.from_user.id)] = "waiting_ton"

# === РЕДАКТИРОВАНИЕ КАРТЫ ===
@dp.callback_query(F.data == "edit_card")
async def edit_card(callback: types.CallbackQuery):
    cursor.execute("SELECT bank_card FROM users WHERE user_id = ?", (callback.from_user.id,))
    result = cursor.fetchone()
    current_card = result[0] if result and result[0] else "не задана"
    text = (
        f"💳 Ваша текущая карта: {current_card}\n\n"
        "Отправьте новый номер карты для изменения или нажмите кнопку ниже для возврата в меню."
    )
    await callback.message.edit_caption(caption=text, reply_markup=back_keyboard)
    await bot.send_message(callback.from_user.id, "Введите новую карту:")
    dp.workflow_data[str(callback.from_user.id)] = "waiting_card"

# === ОБРАБОТКА ВВОДА ДАННЫХ ===
@dp.message()
async def handle_user_input(message: types.Message):
    state = dp.workflow_data.get(str(message.from_user.id))
    if state == "waiting_ton":
        cursor.execute("""
            INSERT INTO users (user_id, ton_wallet)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET ton_wallet=excluded.ton_wallet
        """, (message.from_user.id, message.text))
        conn.commit()
        await message.answer("✅ TON-кошелек успешно обновлён.", reply_markup=main_keyboard)
        dp.workflow_data[str(message.from_user.id)] = None
    elif state == "waiting_card":
        cursor.execute("""
            INSERT INTO users (user_id, bank_card)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET bank_card=excluded.bank_card
        """, (message.from_user.id, message.text))
        conn.commit()
        await message.answer("✅ Карта успешно обновлена.", reply_markup=main_keyboard)
        dp.workflow_data[str(message.from_user.id)] = None

# === ВОЗВРАТ В МЕНЮ ===
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_caption(caption=WELCOME_TEXT, reply_markup=main_keyboard)

# === СТАРТ ===
async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())

