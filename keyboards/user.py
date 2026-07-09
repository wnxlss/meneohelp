from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.ticket import Ticket, TicketStatus


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мои тикеты"), KeyboardButton(text="FAQ")],
            [KeyboardButton(text="Создать тикет")],
        ],
        resize_keyboard=True,
    )


def tickets_inline_keyboard(tickets: list[Ticket]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ticket in tickets:
        status_emoji = "🔴" if ticket.status == TicketStatus.open else "⚫"
        created = ticket.created_at.strftime("%d.%m.%Y")
        builder.button(text=f"{status_emoji} #{ticket.id} {created}", callback_data=f"ticket:view:{ticket.id}")
    builder.adjust(1)
    return builder.as_markup()


def ticket_actions_keyboard(ticket: Ticket) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if ticket.status == TicketStatus.open:
        builder.button(text="Закрыть тикет", callback_data=f"ticket:close:{ticket.id}")
    return builder.as_markup()
