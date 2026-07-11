from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services.support import SupportService


class FloodControlMiddleware(BaseMiddleware):
    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = interval_seconds
        self._last_seen: dict[str, float] = {}

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        if not event.from_user or event.chat.type != "private":
            return await handler(event, data)
        session: AsyncSession = data["session"]
        ticket = await SupportService.get_open_ticket_by_user(session, event.from_user.id)
        ticket_key = str(ticket.id) if ticket else "new"
        key = f"{event.from_user.id}:{ticket_key}"
        now = monotonic()
        last = self._last_seen.get(key, 0.0)
        if now - last < self.interval_seconds:
            await event.answer("Слишком часто. Подождите пару секунд перед следующим сообщением.")
            return None
        self._last_seen[key] = now
        return await handler(event, data)
