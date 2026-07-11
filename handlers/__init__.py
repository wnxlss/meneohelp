from aiogram import Dispatcher

from handlers.admin import router as admin_router
from handlers.sync import router as sync_router
from handlers.user import router as user_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(admin_router)
    dp.include_router(sync_router)
    dp.include_router(user_router)
