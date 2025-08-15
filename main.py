import logging
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode, parse_mode
from aiohttp import web
import aiohttp

# === НАСТРОЙКИ ===
TOKEN = "8481984389:AAHX9_fXrgemHmPeHNuX7pd2xJ1ooDkYgp4"  # вставь токен бота
IMAGE_URL = "https://imgur.com/a/A8aIr3k"  # плейсхолдер картинки
WELCOME_TEXT = (
    "Добро пожаловать в GiftKeeperOTC – надежный P2P-гарант\n\n"
    "💼 Покупайте и продавайте всё, что угодно – безопасно!\n"
    "От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
    "🔹 Удобное управление кошельками\n"
    "🔹 Реферальная система\n\n"
    "Выберите нужный раздел ниже:"
)
UPTIME_URL = "https://replit.com/@artemhasanov201/GiftKeeperOTC#main.py"  # сюда вставь ссылку для пинга

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)

# === КНОПКИ (ИНЛАЙН) ===
keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📥Управление Реквизитами", callback_data="btn1")],
        [InlineKeyboardButton(text="📄Создать сделку", callback_data="btn2")],
        [InlineKeyboardButton(text="🧷Реферальная ссылка", callback_data="btn3")],
        [InlineKeyboardButton(text="📞Тех. Поддержка", callback_data="btn4")]
    ]
)

# === БОТ ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer_photo(
        photo=IMAGE_URL,
        caption=WELCOME_TEXT,
        reply_markup=keyboard
    )

# Обработка нажатий на кнопки (пока просто отвечает)
@dp.callback_query()
async def handle_button(callback: types.CallbackQuery):
    await callback.answer(f"Ты нажал: {callback.data}")

# === WEB-СЕРВЕР ДЛЯ REPLIT ===
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# === ПИНГ UPTIMEROBOT ===
async def ping_uptime():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(UPTIME_URL) as resp:
                    logging.info(f"Uptime ping: {resp.status}")
            except Exception as e:
                logging.error(f"Ping error: {e}")
            await asyncio.sleep(300)  # каждые 5 минут

# === ЗАПУСК ===
async def main():
    await start_webserver()
    asyncio.create_task(ping_uptime())  # запускаем пинг
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
