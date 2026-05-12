from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import Onboarding
from texts import START_TEXT
from keyboards import main_kb
from parser import parse_category_line
from services.users import get_internal_user_id
from services.categories import add_category

router = Router()


@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await get_internal_user_id(message.from_user.id)
    await state.set_state(Onboarding.expense_categories)
    await message.answer(START_TEXT)


@router.message(Onboarding.expense_categories)
async def onboarding_expenses(message: Message, state: FSMContext):
    user_id = await get_internal_user_id(message.from_user.id)

    if message.text.lower().strip() == "готово":
        await state.set_state(Onboarding.income_categories)
        await message.answer(
            "Теперь категории ДОХОДОВ.\n\n"
            "Пример:\n"
            "работа | клиент, зарплата\n"
            "йога | занятие, класс\n\n"
            "Когда закончите, напишите: готово"
        )
        return

    parsed = parse_category_line(message.text)
    if not parsed:
        await message.answer("Не поняла. Формат: категория | псевдоним1, псевдоним2")
        return

    name, aliases = parsed
    await add_category(user_id, "expense", name, aliases)
    await message.answer(f"Добавила расходную категорию: {name}")


@router.message(Onboarding.income_categories)
async def onboarding_incomes(message: Message, state: FSMContext):
    user_id = await get_internal_user_id(message.from_user.id)

    if message.text.lower().strip() == "готово":
        await state.clear()
        await message.answer("Готово. Теперь можно писать операции.", reply_markup=main_kb)
        return

    parsed = parse_category_line(message.text)
    if not parsed:
        await message.answer("Не поняла. Формат: категория | псевдоним1, псевдоним2")
        return

    name, aliases = parsed
    await add_category(user_id, "income", name, aliases)
    await message.answer(f"Добавила доходную категорию: {name}")
