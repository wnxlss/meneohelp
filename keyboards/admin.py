from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Редактировать FAQ", callback_data="admin:faq:edit")
    builder.button(text="Статистика 24 ч", callback_data="admin:stats:1")
    builder.button(text="Статистика 7 д", callback_data="admin:stats:7")
    builder.button(text="Статистика 30 д", callback_data="admin:stats:30")
    builder.button(text="Экспорт тикетов (.csv)", callback_data="admin:export")
    builder.button(text="Блок-лист пользователя", callback_data="admin:blocklist")
    builder.adjust(1)
    return builder.as_markup()
