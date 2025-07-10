import asyncio

from aiogram import Bot, Dispatcher
# from middlewares.database import DatabaseMiddleware # Надо потом переписать класс под новую структуру
from config import TOKEN
from handlers import admin, users

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    # dp.update.middleware(DatabaseMiddleware())

    routers = (admin.router, users.router)
    for router in routers:
        dp.include_router(router)

    await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
    )




if __name__ == "__main__":
    asyncio.run(main())