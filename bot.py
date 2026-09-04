import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
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


def is_owner(message: Message) -> bool:
    return message.from_user and message.from_user.id == OWNER_ID


@router.message(Command("start"))
async def start(message: Message):
    if not is_owner(message):
        return

    await message.answer(
        "Бот запущен.\n\n"
        "/status — состояние аккаунта\n"
        "/logout — выйти из Telegram-аккаунта"
    )


@router.message(Command("status"))
async def status(message: Message):
    if not is_owner(message):
        return

    if client.is_connected() and await client.is_user_authorized():
        await message.answer("✅ Telegram-аккаунт авторизован.")
    else:
        await message.answer("❌ Telegram-аккаунт не авторизован.")


@router.message(Command("logout"))
async def logout(message: Message):
    if not is_owner(message):
        return

    if not client.is_connected():
        await message.answer("Аккаунт уже отключён.")
        return

    try:
        await client.log_out()
        await message.answer(
            "✅ Telegram-аккаунт вышел из текущей сессии."
        )
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    await client.start()

    print("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
