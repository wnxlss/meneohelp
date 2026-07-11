from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from keyboards.user import main_menu_keyboard, ticket_actions_keyboard, tickets_inline_keyboard
from models.ticket import TicketStatus
from services.relay import send_copy
from services.support import SupportService
from utils.message_content import extract_payload

router = Router(name="user")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Просто напишите вопрос в этот чат, и я создам тикет.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.chat.type == "private", F.text == "Создать тикет")
async def create_ticket_hint(message: Message) -> None:
    await message.answer("Просто напишите ваш вопрос или отправьте медиа — тикет создастся автоматически.")


@router.message(F.chat.type == "private", F.text == "FAQ")
async def show_faq(message: Message, session: AsyncSession) -> None:
    faq = await SupportService.get_faq(session, settings.faq_markdown_v2)
    await message.answer(faq, parse_mode="MarkdownV2")


@router.message(F.chat.type == "private", F.text == "Мои тикеты")
async def show_tickets(message: Message, session: AsyncSession) -> None:
    if not message.from_user:
        return
    tickets = await SupportService.list_user_tickets(session, message.from_user.id)
    if not tickets:
        await message.answer("У вас пока нет тикетов.")
        return
    await message.answer("Ваши тикеты:", reply_markup=tickets_inline_keyboard(tickets))


@router.callback_query(F.data.startswith("ticket:view:"))
async def ticket_view(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user:
        return
    if callback.message is None:
        await callback.answer()
        return
    ticket_id = int(callback.data.split(":")[-1])
    ticket = await SupportService.get_ticket_by_id(session, ticket_id, callback.from_user.id)
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    status = "🔴 открыт" if ticket.status == TicketStatus.open else "⚫ закрыт"
    text = f"Тикет #{ticket.id}\nСтатус: {status}\nСоздан: {ticket.created_at:%d.%m.%Y %H:%M}"
    await callback.message.answer(text, reply_markup=ticket_actions_keyboard(ticket))
    await callback.answer()


@router.callback_query(F.data.startswith("ticket:close:"))
async def ticket_close(callback: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    if not callback.data or not callback.from_user:
        return
    if callback.message is None:
        await callback.answer()
        return
    ticket_id = int(callback.data.split(":")[-1])
    ticket = await SupportService.get_ticket_by_id(session, ticket_id, callback.from_user.id)
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    if ticket.status == TicketStatus.closed:
        await callback.answer("Тикет уже закрыт", show_alert=True)
        return
    try:
        await bot.close_forum_topic(chat_id=settings.support_group_id, message_thread_id=ticket.topic_id)
    except Exception:
        pass
    await SupportService.close_ticket(session, ticket)
    await callback.message.answer("Ваш тикет закрыт.")
    await callback.answer("Тикет закрыт")


@router.message(F.chat.type == "private")
async def receive_private_message(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not message.from_user:
        return
    user = await SupportService.ensure_user(session, message.from_user)
    if user.blocked:
        await message.answer("Вы в блок-листе поддержки.")
        return
    ticket = await SupportService.get_open_ticket_by_user(session, user.id)
    if not ticket:
        open_count = await SupportService.count_open_tickets(session, user.id)
        if open_count >= settings.max_open_tickets_per_user:
            await message.answer("У вас уже максимум открытых тикетов. Закройте один из текущих.")
            return
        topic_title = f"Тикет от @{user.username}" if user.username else f"Тикет от {user.full_name}"
        topic = await bot.create_forum_topic(chat_id=settings.support_group_id, name=topic_title)
        topic_id = getattr(topic, "message_thread_id", None)
        if not topic_id:
            await message.answer("Не удалось создать тему тикета. Попробуйте позже.")
            return
        ticket = await SupportService.create_ticket(session, user.id, topic_id)
        if user.username:
            final_title = f"Тикет #{ticket.id} от @{user.username}"
        else:
            final_title = f"Тикет #{ticket.id} от {user.full_name}"
        try:
            await bot.edit_forum_topic(
                chat_id=settings.support_group_id,
                message_thread_id=ticket.topic_id,
                name=final_title,
            )
        except Exception:
            pass
    mirrored = await send_copy(bot, message, settings.support_group_id, ticket.topic_id)
    if ticket.topic_msg_id is None:
        ticket.topic_msg_id = mirrored.message_id
    payload = extract_payload(message)
    await SupportService.save_message(session, ticket.id, "user", payload)
    await message.answer(f"Тикет #{ticket.id} принят. Мы скоро ответим.")
