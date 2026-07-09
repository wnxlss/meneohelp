import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config import settings
from handlers import setup_routers
from middlewares.db import DbSessionMiddleware
from middlewares.flood import FloodControlMiddleware
from services.db import Database
from utils.logging import setup_logging


async def _build_storage():
    try:
        redis = Redis.from_url(settings.redis_dsn)
        await redis.ping()
        return RedisStorage(redis=redis)
    except Exception:
        return MemoryStorage()


async def main() -> None:
    settings.validate()
    setup_logging(settings.log_dir)
    db = Database(settings.database_url)
    await db.create_schema()
    storage = await _build_storage()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DbSessionMiddleware(db))
    dp.message.middleware(FloodControlMiddleware(settings.flood_interval_seconds))
    setup_routers(dp)
    try:
        logging.info("bot_started")
        await dp.start_polling(bot)
    finally:
        await db.dispose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
