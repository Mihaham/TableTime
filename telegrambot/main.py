import asyncio
import sys
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.exceptions import TelegramNetworkError, TelegramAPIError
# from middlewares.database import DatabaseMiddleware # Надо потом переписать класс под новую структуру
from config import TOKEN
from handlers import admin, users, rps, diceladders

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Global error handler
async def errors_handler(update: Update, exception: Exception):
    """Handle all exceptions"""
    try:
        if isinstance(exception, TelegramNetworkError):
            logger.error(f"Telegram network error: {exception}", exc_info=True)
            # Network errors are usually transient, just log them
            return True
        elif isinstance(exception, TelegramAPIError):
            logger.error(f"Telegram API error: {exception}", exc_info=True)
            return True
        else:
            logger.error(f"Unhandled exception: {exception}", exc_info=True)
            return True
    except Exception as e:
        logger.error(f"Error in error handler: {e}", exc_info=True)
        return True

async def main():
    # dp.update.middleware(DatabaseMiddleware())
    
    # Register global error handler
    dp.errors.register(errors_handler)

    routers = (admin.router, users.router, rps.router, diceladders.router)
    for router in routers:
        dp.include_router(router)

    await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
    )




if __name__ == "__main__":
    asyncio.run(main())