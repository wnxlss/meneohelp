from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from keyboards.admin import admin_panel_keyboard
from services.support import SupportService
from utils.states import AdminStates

router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        return
    await message.answer("Панель администратора", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin:faq:edit")
async def admin_faq_edit(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.from_user or not _is_admin(callback.from_user.id):
        return
    if callback.message is None:
        await callback.answer()
        return
    await state.set_state(AdminStates.waiting_faq)
    await callback.message.answer("Отправьте новый FAQ в MarkdownV2.")
    await callback.answer()


@router.message(AdminStates.waiting_faq)
async def admin_faq_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        return
    if not message.text:
        await message.answer("Нужен текст FAQ.")
        return
    await SupportService.set_faq(session, message.text)
    await state.clear()
    await message.answer("FAQ обновлён.")


@router.callback_query(F.data.startswith("admin:stats:"))
async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not _is_admin(callback.from_user.id):
        return
    if callback.message is None:
        await callback.answer()
        return
    if not callback.data:
        return
    days = int(callback.data.split(":")[-1])
    stat = await SupportService.build_stats(session, days)
    await callback.message.answer(
        f"Статистика за {stat.period}\nВсего: {stat.total}\nОткрытых: {stat.open_count}\nЗакрытых: {stat.closed_count}"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:export")
async def admin_export(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not _is_admin(callback.from_user.id):
        return
    if callback.message is None:
        await callback.answer()
        return
    csv_content = await SupportService.export_tickets_csv(session)
    csv_bytes = csv_content.encode("utf-8")
    await callback.message.answer_document(
        document=BufferedInputFile(csv_bytes, filename="tickets_export.csv"),
        caption="Экспорт тикетов",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:blocklist")
async def admin_blocklist(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.from_user or not _is_admin(callback.from_user.id):
        return
    if callback.message is None:
        await callback.answer()
        return
    await state.set_state(AdminStates.waiting_block_user)
    await callback.message.answer("Отправьте: user_id on|off")
    await callback.answer()


@router.message(AdminStates.waiting_block_user)
async def admin_blocklist_apply(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        return
    if not message.text:
        await message.answer("Неверный формат.")
        return
    parts = message.text.strip().split()
    if len(parts) != 2 or parts[1] not in {"on", "off"}:
        await message.answer("Используйте формат: user_id on|off")
        return
    user_id = int(parts[0])
    blocked = parts[1] == "on"
    user = await SupportService.set_user_blocked(session, user_id, blocked)
    if not user:
        await message.answer("Пользователь не найден.")
        return
    await state.clear()
    await message.answer(f"Пользователь {user_id} {'заблокирован' if blocked else 'разблокирован'}.")
