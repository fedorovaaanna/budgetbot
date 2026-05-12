import asyncio
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, TZ
from db import init_db
from services.cleanup import cleanup_old_transactions
from services.notifications import send_daily_notifications

from handlers.onboarding import router as onboarding_router
from handlers.common import router as common_router
from handlers.payments import router as payments_router
from handlers.personal import router as personal_router
from handlers.family import router as family_router
from handlers.transactions import router as transactions_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(onboarding_router)
    dp.include_router(common_router)
    dp.include_router(payments_router)
    dp.include_router(personal_router)
    dp.include_router(family_router)
    dp.include_router(transactions_router)

    await init_db()
    await cleanup_old_transactions()

    scheduler = AsyncIOScheduler(timezone=str(TZ))
    scheduler.add_job(partial(send_daily_notifications, bot), "interval", minutes=1)
    scheduler.add_job(cleanup_old_transactions, "cron", hour=4, minute=0)
    scheduler.start()

    print("Budget bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
