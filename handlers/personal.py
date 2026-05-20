from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import TZ
from keyboards import main_kb
from utils import money, tx_sign, parse_amount
from parser import parse_category_line
from services.users import get_internal_user_id, has_access
from services.stats import get_personal_stats, format_stats
from services.history import get_personal_history
from services.settings import set_user_piggy_start_balance
from services.categories import (
    add_category,
    get_categories,
    rename_category,
    set_category_aliases,
    disable_category,
)

router = Router()


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def stats_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    if not await has_access(user_id):
        await message.answer("⛔ Тестовый доступ закончился. Используйте /pay.")
        return
    stats = await get_personal_stats(user_id)
    await message.answer(format_stats(stats, "Личный бюджет"), reply_markup=main_kb)


@router.message(Command("piggy"))
async def piggy_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    if not await has_access(user_id):
        await message.answer("⛔ Тестовый доступ закончился. Используйте /pay.")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2:
        value = parse_amount(parts[1].strip())
        if value is None:
            await message.answer("Формат: /piggy 10000")
            return
        await set_user_piggy_start_balance(user_id, float(value))

    stats = await get_personal_stats(user_id)
    await message.answer(
        f"Копилка сейчас: {money(stats.get('piggy_balance'))} (старт {money(stats.get('piggy_start_balance'))})\n"
        f"Команда: /piggy 10000 — задать стартовую сумму.",
        reply_markup=main_kb,
    )


@router.message(Command("history"))
@router.message(F.text == "🧾 История")
async def history_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    if not await has_access(user_id):
        await message.answer("⛔ Тестовый доступ закончился. Используйте /pay.")
        return
    rows = await get_personal_history(user_id)
    if not rows:
        await message.answer("История пустая.")
        return

    text = "🧾 Личная история:\n\n"
    for type_, is_extra, amount, category, comment, created_at in rows:
        dt = datetime.fromisoformat(created_at).astimezone(TZ).strftime("%d.%m %H:%M")
        sign = tx_sign(type_, is_extra)
        comment_text = f" — {comment}" if comment else ""
        text += f"{dt} | {sign}{money(amount)} | {category}{comment_text}\n"

    await message.answer(text, reply_markup=main_kb)


@router.message(Command("categories"))
@router.message(F.text == "⚙️ Категории")
async def categories_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    rows = await get_categories(user_id, active_only=False)

    if not rows:
        await message.answer("Категорий пока нет.")
        return

    text = "⚙️ Личные категории\n\n"
    for cid, type_, name, aliases, is_active in rows:
        status = "" if is_active else " удалена"
        type_title = "доход" if type_ == "income" else "расход"
        aliases_text = f" | {aliases}" if aliases else ""
        text += f"#{cid} {type_title}: {name}{aliases_text}{status}\n"

    text += (
        "\nКоманды:\n"
        "/add_category expense еда | кафе, продукты\n"
        "/add_category income работа | клиент, зарплата\n"
        "/rename_category 3 новое название\n"
        "/aliases_category 3 кафе, ресторан\n"
        "/delete_category 3"
    )
    await message.answer(text)


@router.message(Command("add_category"))
async def add_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or parts[1] not in ["income", "expense"]:
        await message.answer("Формат: /add_category expense еда | кафе, продукты")
        return
    parsed = parse_category_line(parts[2])
    if not parsed:
        await message.answer("Не поняла категорию.")
        return
    name, aliases = parsed
    await add_category(user_id, parts[1], name, aliases)
    await message.answer(f"Добавила категорию: {name}")


@router.message(Command("rename_category"))
async def rename_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Формат: /rename_category 3 новое название")
        return
    count = await rename_category(user_id, int(parts[1]), parts[2].strip())
    await message.answer("Переименовала." if count else "Категория не найдена.")


@router.message(Command("aliases_category"))
async def aliases_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Формат: /aliases_category 3 кафе, ресторан, доставка")
        return
    count = await set_category_aliases(user_id, int(parts[1]), parts[2].strip())
    await message.answer("Псевдонимы обновлены." if count else "Категория не найдена.")


@router.message(Command("delete_category"))
async def delete_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Формат: /delete_category 3")
        return
    count = await disable_category(user_id, int(parts[1]))
    await message.answer("Категория отключена." if count else "Категория не найдена.")
