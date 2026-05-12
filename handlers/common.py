from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from keyboards import main_kb
from texts import format_help
from utils import valid_time
from services.users import get_internal_user_id, has_access
from services.settings import set_notifications, set_family_notifications, set_notify_time
from services.exporter import export_excel

router = Router()


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def help_handler(message: Message):
    await message.answer(format_help(), reply_markup=main_kb)


@router.message(Command("notifications_on"))
async def notifications_on(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    await set_notifications(user_id, 1)
    await message.answer("Личные утренние и вечерние уведомления включены.")


@router.message(Command("notifications_off"))
async def notifications_off(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    await set_notifications(user_id, 0)
    await message.answer("Личные уведомления выключены.")


@router.message(Command("family_notifications_on"))
async def family_notifications_on(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    await set_family_notifications(user_id, 1)
    await message.answer("Семейные уведомления включены.")


@router.message(Command("family_notifications_off"))
async def family_notifications_off(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    await set_family_notifications(user_id, 0)
    await message.answer("Семейные уведомления выключены.")


@router.message(Command("notify_time"))
async def notify_time(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    parts = message.text.split()
    if len(parts) != 3 or not valid_time(parts[1]) or not valid_time(parts[2]):
        await message.answer("Формат: /notify_time 09:00 21:00")
        return
    await set_notify_time(user_id, parts[1], parts[2])
    await message.answer(f"Время уведомлений обновлено: утро {parts[1]}, вечер {parts[2]}.")


@router.message(Command("export"))
@router.message(F.text == "📤 Excel")
async def export_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    if not await has_access(user_id):
        await message.answer("⛔ Тестовый доступ закончился. Используйте /pay.")
        return
    file_path = await export_excel(user_id)
    await message.answer_document(FSInputFile(file_path), caption="Готово. Экспорт бюджета в Excel.")
