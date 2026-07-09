from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from services.relay import send_copy
from services.support import SupportService
from utils.message_content import extract_payload

router = Router(name="sync")

_RELAY_CONTENT_TYPES = {
    ContentType.TEXT,
    ContentType.PHOTO,
    ContentType.DOCUMENT,
    ContentType.VIDEO,
    ContentType.AUDIO,
    ContentType.VOICE,
    ContentType.STICKER,
    ContentType.VIDEO_NOTE,
    ContentType.ANIMATION,
}


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(F.chat.id == settings.support_group_id, F.forum_topic_closed)
async def on_topic_closed(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not message.message_thread_id:
        return
    ticket = await SupportService.get_ticket_by_topic(session, message.message_thread_id)
    if not ticket or ticket.status.value == "closed":
        return
    await SupportService.close_ticket(session, ticket)
    await bot.send_message(
        ticket.user_id,
        f"✅ Ваше обращение обработано. Тикет #{ticket.id} закрыт.",
    )


@router.message(
    F.chat.id == settings.support_group_id,
    F.message_thread_id.as_("thread_id"),
    F.content_type.in_(_RELAY_CONTENT_TYPES),
)
async def sync_topic_to_user(message: Message, bot: Bot, session: AsyncSession, thread_id: int) -> None:
    if not message.from_user or message.from_user.is_bot:
        return
    if not _is_admin(message.from_user.id):
        return
    if message.forward_date:
        return
    ticket = await SupportService.get_ticket_by_topic(session, thread_id)
    if not ticket or ticket.status.value == "closed":
        return
    await send_copy(bot, message, ticket.user_id)
    payload = extract_payload(message)
    await SupportService.save_message(session, ticket.id, "admin", payload)
