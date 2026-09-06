import asyncio
import os
import tempfile

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from telethon import TelegramClient

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))

router = Router()

client = TelegramClient(
    "telegram_account",
    API_ID,
    API_HASH
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статус")],
        [KeyboardButton(text="🚪 Выйти из сессии"), KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


def is_owner(message: Message) -> bool:
    return message.from_user and message.from_user.id == OWNER_ID


@router.message(Command("start"))
async def start(message: Message):
    if not is_owner(message):
        return

    await message.answer(
        "<b>Панель управления</b>\n\n"
        "Выбери действие на клавиатуре ниже.",
        reply_markup=main_menu,
        parse_mode="HTML",
    )


@router.message(Command("status"))
async def status(message: Message):
    if not is_owner(message):
        return

    if client.is_connected() and await client.is_user_authorized():
        await message.answer("✅ Telegram-аккаунт авторизован.")
    else:
        await message.answer("❌ Telegram-аккаунт не авторизован.")


@router.message(lambda message: message.text == "📊 Статус")
async def status_button(message: Message):
    await status(message)


@router.message(lambda message: message.text == "ℹ️ Помощь")
async def help_button(message: Message):
    if not is_owner(message):
        return

    await message.answer(
        "<b>Доступные действия</b>\n\n"
        "📊 Статус — проверить авторизацию Telegram-аккаунта.\n"
        "🚪 Выйти из сессии — завершить авторизацию и удалить локальную сессию.",
        parse_mode="HTML",
    )


@router.message(Command("logout"))
async def logout(message: Message):
    if not is_owner(message):
        return

    if not client.is_connected():
        await message.answer("Аккаунт уже отключён.")
        return

    try:
        await client.log_out()
        session_file = "telegram_account.session"
        if os.path.exists(session_file):
            os.remove(session_file)
        await message.answer(
            "✅ Telegram-аккаунт вышел из текущей сессии."
        )
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(lambda message: message.text == "🚪 Выйти из сессии")
async def logout_button(message: Message):
    await logout(message)


@router.message(lambda message: message.document is not None)
async def session_file(message: Message):
    if not is_owner(message):
        return

    filename = message.document.file_name or ""
    if not filename.lower().endswith(".session"):
        await message.answer("❌ Отправь файл с расширением .session.")
        return

    session_path = ""
    uploaded_client = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".session", delete=False) as temp_file:
            session_path = temp_file.name

        await message.bot.download(message.document, destination=session_path)
        uploaded_client = TelegramClient(session_path, API_ID, API_HASH)
        await uploaded_client.connect()

        if not await uploaded_client.is_user_authorized():
            await message.answer("❌ Эта сессия недействительна или уже завершена.")
            return

        await uploaded_client.log_out()
        await message.answer(
            "✅ Из отправленной .session вышел. Локальный файл удалён."
        )
    except Exception as error:
        await message.answer(f"❌ Не удалось обработать сессию: {error}")
    finally:
        if uploaded_client and uploaded_client.is_connected():
            await uploaded_client.disconnect()
        if session_path and os.path.exists(session_path):
            os.remove(session_path)


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
