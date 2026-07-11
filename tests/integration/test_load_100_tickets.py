import asyncio
from time import perf_counter

import pytest
from aiogram.types import User as TgUser

from services.support import SupportService


@pytest.mark.asyncio
async def test_load_100_concurrent_tickets(session_factory):
    async def create_one(i: int):
        async with session_factory() as local_session:
            user = await SupportService.ensure_user(
                local_session,
                TgUser(id=10000 + i, is_bot=False, first_name=f"User{i}", username=f"user{i}"),
            )
            ticket = await SupportService.create_ticket(local_session, user.id, topic_id=50000 + i)
            await local_session.commit()
            return ticket.id

    started = perf_counter()
    result = await asyncio.gather(*(create_one(i) for i in range(100)))
    elapsed_ms = (perf_counter() - started) * 1000
    assert len(result) == 100
    assert elapsed_ms < 300
