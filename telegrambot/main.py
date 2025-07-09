import asyncio

from aiogram import Bot, Dispatcher
from middlewares.database import DatabaseMiddleware
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.update.middleware(DatabaseMiddleware())

    routers = ()
    for router in routers:
        dp.include_router(router)

    await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
    )




if __name__ == "__main__":
    asyncio.run(main())