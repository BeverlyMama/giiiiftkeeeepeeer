import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# === НАСТРОЙКИ ===
TOKEN = "8481984389:AAHX9_fXrgemHmPeHNuX7pd2xJ1ooDkYgp4"
IMAGE_URL = "https://imgur.com/a/A8aIr3k"
BOT_USERNAME = "@GiftsKeeperOTCBot"  # поменяй на username своего бота

WELCOME_TEXT = (
    "Добро пожаловать в GiftKeeperOTC – надежный P2P-гарант\n\n"
    "💼 Покупайте и продавайте всё, что угодно – безопасно!\n"
    "От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
    "🔹 Удобное управление кошельками\n"
    "🔹 Реферальная система\n\n"
    "Выберите нужный раздел ниже:"
)

logging.basicConfig(level=logging.INFO)

# === БАЗА ДАННЫХ ===
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ton_wallet TEXT,
    bank_card TEXT,
    referrer_id INTEGER,
    referrals_count INTEGER DEFAULT 0,
    earned REAL DEFAULT 0.0
)
""")
conn.commit()

# === КНОПКИ ===
main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📥Управление Реквизитами", callback_data="manage_requisites")],
        [InlineKeyboardButton(text="📄Создать сделку", callback_data="create_deal")],
        [InlineKeyboardButton(text="🧷Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton(text="📞Тех. Поддержка", url="https://t.me/giftkeepersupp")]  # 👈 сюда вставишь ссылку
    ]
)

manage_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🌑Добавить/изменить TON-кошелек", callback_data="edit_ton")],
        [InlineKeyboardButton(text="💳Добавить/изменить карту", callback_data="edit_card")],
        [InlineKeyboardButton(text="🔙Вернуться в меню", callback_data="back_to_main")]
    ]
)

back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙Вернуться в меню", callback_data="back_to_main")]
    ]
)

# === FSM состояния ===
class EditWallet(StatesGroup):
    waiting_ton = State()
    waiting_card = State()

# === БОТ ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# === ОБРАБОТКА /start с рефералом ===
@dp.message(F.text.startswith("/start"))
async def start_cmd(message: types.Message):
    args = message.text.split()
    ref_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].replace("ref_", ""))
        except ValueError:
            ref_id = None

    cursor.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (message.from_user.id, ref_id))
        conn.commit()
        if ref_id and ref_id != message.from_user.id:
            # Начисляем бонус пригласившему
            cursor.execute("UPDATE users SET referrals_count = referrals_count + 1, earned = earned + 0.1 WHERE user_id=?", (ref_id,))
            conn.commit()

    await message.answer_photo(
        photo=IMAGE_URL,
        caption=WELCOME_TEXT,
        reply_markup=main_keyboard
    )

# === УПРАВЛЕНИЕ РЕКВИЗИТАМИ ===
@dp.callback_query(F.data == "manage_requisites")
async def manage_requisites(callback: types.CallbackQuery):
    text = (
        "📥Управление реквизитами\n\n"
        "Используйте кнопки ниже чтобы добавить/изменить реквизиты\n"
        "👇"
    )
    await callback.message.edit_caption(caption=text, reply_markup=manage_keyboard)

# === РЕДАКТИРОВАНИЕ TON-КОШЕЛЬКА ===
@dp.callback_query(F.data == "edit_ton")
async def edit_ton(callback: types.CallbackQuery, state: FSMContext):
    cursor.execute("SELECT ton_wallet FROM users WHERE user_id = ?", (callback.from_user.id,))
    result = cursor.fetchone()
    current_wallet = result[0] if result and result[0] else "не указан"
    text = (
        f"💼Ваш текущий TON-кошелек: {current_wallet}\n\n"
        "Отправьте новый адрес кошелька для изменения."
    )
    await callback.message.edit_caption(caption=text, reply_markup=back_keyboard)
    await state.set_state(EditWallet.waiting_ton)

# === РЕДАКТИРОВАНИЕ КАРТЫ ===
@dp.callback_query(F.data == "edit_card")
async def edit_card(callback: types.CallbackQuery, state: FSMContext):
    cursor.execute("SELECT bank_card FROM users WHERE user_id = ?", (callback.from_user.id,))
    result = cursor.fetchone()
    current_card = result[0] if result and result[0] else "не указана"
    text = (
        f"💳Ваша текущая карта: {current_card}\n\n"
        "Отправьте новый номер карты для изменения."
    )
    await callback.message.edit_caption(caption=text, reply_markup=back_keyboard)
    await state.set_state(EditWallet.waiting_card)

# === ОБРАБОТКА ВВОДА ДАННЫХ ===
@dp.message(EditWallet.waiting_ton, F.text)
async def process_ton(message: types.Message, state: FSMContext):
    cursor.execute("""
        INSERT INTO users (user_id, ton_wallet)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET ton_wallet=excluded.ton_wallet
    """, (message.from_user.id, message.text))
    conn.commit()

    await message.answer("✅ Кошелек успешно обновлен.")
    await message.answer_photo(photo=IMAGE_URL, caption=WELCOME_TEXT, reply_markup=main_keyboard)
    await state.clear()

@dp.message(EditWallet.waiting_card, F.text)
async def process_card(message: types.Message, state: FSMContext):
    cursor.execute("""
        INSERT INTO users (user_id, bank_card)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET bank_card=excluded.bank_card
    """, (message.from_user.id, message.text))
    conn.commit()

    await message.answer("✅ Карта успешно обновлена.")
    await message.answer_photo(photo=IMAGE_URL, caption=WELCOME_TEXT, reply_markup=main_keyboard)
    await state.clear()

# === РЕФЕРАЛЬНАЯ СИСТЕМА ===
@dp.callback_query(F.data == "ref_link")
async def ref_link(callback: types.CallbackQuery):
    cursor.execute("SELECT referrals_count, earned FROM users WHERE user_id=?", (callback.from_user.id,))
    result = cursor.fetchone()
    referrals_count = result[0] if result else 0
    earned = result[1] if result else 0.0

    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{callback.from_user.id}"

    text = (
        f"🔗Ваша реферальная ссылка:\n{ref_link}\n\n"
        f"👥Количество рефералов: {referrals_count}\n"
        f"💰Заработанно с рефералов: {earned:.1f} TON"
    )

    await callback.message.edit_caption(caption=text, reply_markup=back_keyboard)

# === ВОЗВРАТ В МЕНЮ ===
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_caption(caption=WELCOME_TEXT, reply_markup=main_keyboard)

# === СТАРТ ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
