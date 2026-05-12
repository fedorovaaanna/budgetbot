from aiogram import Router
from aiogram.types import Message

from config import PROMO_CODE
from keyboards import main_kb
from utils import money
from parser import parse_transaction
from services.users import get_internal_user_id, has_access, activate_paid
from services.transactions import save_personal_transaction, save_family_transaction

router = Router()


@router.message()
async def any_message_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)

    if message.text and message.text.strip() == PROMO_CODE:
        await activate_paid(user_id)
        await message.answer("🎉 Промокод принят. Lifetime-доступ активирован.", reply_markup=main_kb)
        return

    if not await has_access(user_id):
        await message.answer("⛔ Тестовый доступ закончился. Используйте /pay.")
        return

    parsed = parse_transaction(message.text or "")
    if not parsed:
        return

    if parsed["scope"] == "family":
        category, cleaned_comment, error = await save_family_transaction(user_id, parsed)
        if error == "no_family":
            await message.answer("Сначала создайте семейный бюджет: /family_create")
            return
        operation_scope = "Семейный бюджет"
    else:
        category, cleaned_comment = await save_personal_transaction(user_id, parsed)
        operation_scope = "Личный бюджет"

    operation = "Доход" if parsed["type"] == "income" else "Расход"
    if parsed["is_extra"]:
        operation = "Вне бюджета: " + operation

    comment_text = f"\nКомментарий: {cleaned_comment}" if cleaned_comment else ""

    await message.answer(
        f"✅ {operation_scope}\n"
        f"{operation}: {money(parsed['amount'])}\n"
        f"Категория: {category}"
        f"{comment_text}",
        reply_markup=main_kb,
    )
