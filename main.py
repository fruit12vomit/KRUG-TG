import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import API_TOKEN
from handlers import router

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.set_my_commands([
        BotCommand(command="start", description="⭕️ Запустить КРУЖОК")
    ])
    print("⭕️ КРУЖОК запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
