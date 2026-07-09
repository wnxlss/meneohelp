from datetime import datetime, timezone

import pytest
from aiogram.types import User as TgUser

from models.ticket import TicketStatus
from services.support import SupportService
from utils.message_content import MessagePayload


@pytest.mark.asyncio
async def test_create_ticket(session):
    user = await SupportService.ensure_user(
        session,
        TgUser(id=1001, is_bot=False, first_name="Test", username="tester"),
    )
    ticket = await SupportService.create_ticket(session, user.id, topic_id=777)
    await session.commit()
    fetched = await SupportService.get_ticket_by_id(session, ticket.id, user.id)
    assert fetched is not None
    assert fetched.status == TicketStatus.open
    assert fetched.topic_id == 777


@pytest.mark.asyncio
async def test_close_ticket(session):
    user = await SupportService.ensure_user(
        session,
        TgUser(id=1002, is_bot=False, first_name="Test", username="tester2"),
    )
    ticket = await SupportService.create_ticket(session, user.id, topic_id=778)
    await SupportService.close_ticket(session, ticket)
    await session.commit()
    fetched = await SupportService.get_ticket_by_id(session, ticket.id, user.id)
    assert fetched is not None
    assert fetched.status == TicketStatus.closed
    assert fetched.closed_at is not None


@pytest.mark.asyncio
async def test_sync_message_store(session):
    user = await SupportService.ensure_user(
        session,
        TgUser(id=1003, is_bot=False, first_name="Test", username="tester3"),
    )
    ticket = await SupportService.create_ticket(session, user.id, topic_id=779)
    payload = MessagePayload(
        text="Не могу оплатить",
        file_id=None,
        file_type=None,
        sent_at=datetime.now(timezone.utc),
    )
    msg = await SupportService.save_message(session, ticket.id, "user", payload)
    await session.commit()
    assert msg.ticket_id == ticket.id
    assert msg.text == "Не могу оплатить"
