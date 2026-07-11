from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import StringIO

from aiogram.types import User as TgUser
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Message, Setting, Ticket, TicketStatus, User
from utils.message_content import MessagePayload


@dataclass(slots=True)
class TicketStat:
    period: str
    total: int
    open_count: int
    closed_count: int


class SupportService:
    FAQ_KEY = "faq_markdown_v2"

    @staticmethod
    async def ensure_user(session: AsyncSession, tg_user: TgUser) -> User:
        user = await session.get(User, tg_user.id)
        if user:
            user.username = tg_user.username
            user.full_name = tg_user.full_name
            return user
        user = User(id=tg_user.id, username=tg_user.username, full_name=tg_user.full_name)
        session.add(user)
        await session.flush()
        return user

    @staticmethod
    async def count_open_tickets(session: AsyncSession, user_id: int) -> int:
        query = select(func.count(Ticket.id)).where(Ticket.user_id == user_id, Ticket.status == TicketStatus.open)
        return int(await session.scalar(query) or 0)

    @staticmethod
    async def create_ticket(
        session: AsyncSession,
        user_id: int,
        topic_id: int,
        topic_msg_id: int | None = None,
    ) -> Ticket:
        ticket = Ticket(
            user_id=user_id,
            topic_id=topic_id,
            topic_msg_id=topic_msg_id,
            status=TicketStatus.open,
        )
        session.add(ticket)
        await session.flush()
        return ticket

    @staticmethod
    async def get_open_ticket_by_user(session: AsyncSession, user_id: int) -> Ticket | None:
        query = (
            select(Ticket)
            .where(Ticket.user_id == user_id, Ticket.status == TicketStatus.open)
            .order_by(Ticket.created_at.desc())
            .limit(1)
        )
        return await session.scalar(query)

    @staticmethod
    async def get_ticket_by_id(session: AsyncSession, ticket_id: int, user_id: int | None = None) -> Ticket | None:
        query = select(Ticket).where(Ticket.id == ticket_id)
        if user_id is not None:
            query = query.where(Ticket.user_id == user_id)
        return await session.scalar(query)

    @staticmethod
    async def get_ticket_by_topic(session: AsyncSession, topic_id: int) -> Ticket | None:
        return await session.scalar(select(Ticket).where(Ticket.topic_id == topic_id))

    @staticmethod
    async def list_user_tickets(session: AsyncSession, user_id: int) -> list[Ticket]:
        query = select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.created_at.desc())
        return list(await session.scalars(query))

    @staticmethod
    async def close_ticket(session: AsyncSession, ticket: Ticket) -> None:
        ticket.status = TicketStatus.closed
        ticket.closed_at = datetime.now(timezone.utc)
        await session.flush()

    @staticmethod
    async def save_message(session: AsyncSession, ticket_id: int, from_user: str, payload: MessagePayload) -> Message:
        entry = Message(
            ticket_id=ticket_id,
            from_user=from_user,
            text=payload.text,
            file_id=payload.file_id,
            file_type=payload.file_type,
            sent_at=payload.sent_at,
        )
        session.add(entry)
        await session.flush()
        return entry

    @staticmethod
    async def get_faq(session: AsyncSession, fallback: str) -> str:
        item = await session.get(Setting, SupportService.FAQ_KEY)
        return item.value if item else fallback

    @staticmethod
    async def set_faq(session: AsyncSession, value: str) -> None:
        item = await session.get(Setting, SupportService.FAQ_KEY)
        if item:
            item.value = value
        else:
            session.add(Setting(key=SupportService.FAQ_KEY, value=value))
        await session.flush()

    @staticmethod
    async def build_stats(session: AsyncSession, days: int) -> TicketStat:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        total_query = select(func.count(Ticket.id)).where(Ticket.created_at >= since)
        open_query = select(func.count(Ticket.id)).where(Ticket.created_at >= since, Ticket.status == TicketStatus.open)
        closed_query = select(func.count(Ticket.id)).where(
            Ticket.created_at >= since,
            Ticket.status == TicketStatus.closed,
        )
        return TicketStat(
            period=f"{days} д.",
            total=int(await session.scalar(total_query) or 0),
            open_count=int(await session.scalar(open_query) or 0),
            closed_count=int(await session.scalar(closed_query) or 0),
        )

    @staticmethod
    async def export_tickets_csv(session: AsyncSession) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ticket_id", "user_id", "status", "created_at", "closed_at", "topic_id"])
        query = select(Ticket).order_by(Ticket.created_at.desc())
        for ticket in await session.scalars(query):
            writer.writerow(
                [
                    ticket.id,
                    ticket.user_id,
                    ticket.status.value,
                    ticket.created_at.isoformat() if ticket.created_at else "",
                    ticket.closed_at.isoformat() if ticket.closed_at else "",
                    ticket.topic_id,
                ]
            )
        return output.getvalue()

    @staticmethod
    async def set_user_blocked(session: AsyncSession, user_id: int, blocked: bool) -> User | None:
        user = await session.get(User, user_id)
        if not user:
            return None
        user.blocked = blocked
        await session.flush()
        return user
