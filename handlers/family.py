from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import TZ
from keyboards import main_kb
from utils import money, tx_sign
from parser import parse_category_line
from services.users import get_internal_user_id, has_access
from services.family import (
    get_user_family,
    create_family,
    join_family,
    add_family_category,
    get_family_categories,
    rename_family_category,
    set_family_category_aliases,
    disable_family_category,
)
from services.stats import get_family_stats, format_stats
from services.history import get_family_history

router = Router()


@router.message(Command("family_create"))
async def family_create_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    if not await has_access(user_id):
        await message.answer("⛔ Семейный бюджет доступен после оплаты или во время trial.")
        return
    family_id, invite_code, created = await create_family(user_id)
    if created:
        await message.answer(
            f"👨‍👩‍👧 Семейный бюджет создан.\n\n"
            f"Код приглашения:\n{invite_code}\n\n"
            f"Второй человек должен написать боту:\n/family_join {invite_code}\n\n"
            f"Семейные операции вводятся с f:\nf -40 продукты"
        )
    else:
        await message.answer(f"У вас уже есть семейный бюджет.\n\nКод приглашения:\n{invite_code}")


@router.message(Command("family_join"))
async def family_join_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /family_join FAM-12345")
        return
    family_id, status = await join_family(user_id, parts[1].strip())
    if status == "not_found":
        await message.answer("Семейный бюджет с таким кодом не найден.")
    elif status == "full":
        await message.answer("В этом семейном бюджете уже 2 участника.")
    elif status == "already":
        await message.answer("Вы уже в этом семейном бюджете.")
    elif status == "joined":
        await message.answer("Вы присоединились к семейному бюджету.\n\nТеперь можно писать:\nf -40 продукты\nf +1000 зарплата")


@router.message(Command("family_stats"))
async def family_stats_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    family = await get_user_family(user_id)
    if not family:
        await message.answer("У вас пока нет семейного бюджета. Создать: /family_create")
        return
    stats = await get_family_stats(family[0])
    await message.answer(format_stats(stats, "Семейный бюджет"), reply_markup=main_kb)


@router.message(Command("family_history"))
async def family_history_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    family = await get_user_family(user_id)
    if not family:
        await message.answer("У вас пока нет семейного бюджета.")
        return
    rows = await get_family_history(family[0])
    if not rows:
        await message.answer("Семейная история пустая.")
        return
    text = "🧾 Семейная история:\n\n"
    for member_number, type_, is_extra, amount, category, comment, created_at in rows:
        dt = datetime.fromisoformat(created_at).astimezone(TZ).strftime("%d.%m %H:%M")
        sign = tx_sign(type_, is_extra)
        comment_text = f" — {comment}" if comment else ""
        text += f"{dt} | участник #{member_number} | {sign}{money(amount)} | {category}{comment_text}\n"
    await message.answer(text)


@router.message(Command("family_categories"))
async def family_categories_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    family = await get_user_family(user_id)
    if not family:
        await message.answer("У вас пока нет семейного бюджета. Создать: /family_create")
        return
    rows = await get_family_categories(family[0], active_only=False)
    if not rows:
        await message.answer(
            "Семейных категорий пока нет.\n\n"
            "Добавить:\n"
            "/family_add_category expense продукты | магазин, еда\n"
            "/family_add_category income зарплата | зп, работа"
        )
        return
    text = "👨‍👩‍👧 Семейные категории\n\n"
    for cid, type_, name, aliases, is_active in rows:
        status = "" if is_active else " удалена"
        type_title = "доход" if type_ == "income" else "расход"
        aliases_text = f" | {aliases}" if aliases else ""
        text += f"#{cid} {type_title}: {name}{aliases_text}{status}\n"
    text += (
        "\nКоманды:\n"
        "/family_add_category expense продукты | магазин, еда\n"
        "/family_add_category income зарплата | зп, работа\n"
        "/family_rename_category 3 новое название\n"
        "/family_aliases_category 3 магазин, супермаркет\n"
        "/family_delete_category 3"
    )
    await message.answer(text)


@router.message(Command("family_add_category"))
async def family_add_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    family = await get_user_family(user_id)
    if not family:
        await message.answer("Сначала создайте семейный бюджет: /family_create")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or parts[1] not in ["income", "expense"]:
        await message.answer("Формат: /family_add_category expense продукты | магазин, еда")
        return
    parsed = parse_category_line(parts[2])
    if not parsed:
        await message.answer("Не поняла категорию.")
        return
    name, aliases = parsed
    await add_family_category(family[0], parts[1], name, aliases)
    await message.answer(f"Добавила семейную категорию: {name}")


@router.message(Command("family_rename_category"))
async def family_rename_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    family = await get_user_family(user_id)
    if not family:
        await message.answer("У вас пока нет семейного бюджета.")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Формат: /family_rename_category 3 новое название")
        return
    count = await rename_family_category(family[0], int(parts[1]), parts[2].strip())
    await message.answer("Переименовала." if count else "Категория не найдена.")


@router.message(Command("family_aliases_category"))
async def family_aliases_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    family = await get_user_family(user_id)
    if not family:
        await message.answer("У вас пока нет семейного бюджета.")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Формат: /family_aliases_category 3 магазин, супермаркет")
        return
    count = await set_family_category_aliases(family[0], int(parts[1]), parts[2].strip())
    await message.answer("Псевдонимы обновлены." if count else "Категория не найдена.")


@router.message(Command("family_delete_category"))
async def family_delete_category_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    family = await get_user_family(user_id)
    if not family:
        await message.answer("У вас пока нет семейного бюджета.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Формат: /family_delete_category 3")
        return
    count = await disable_family_category(family[0], int(parts[1]))
    await message.answer("Категория отключена." if count else "Категория не найдена.")


@router.message(F.text == "👨‍👩‍👧 Семья")
async def family_button(message: Message):
    await message.answer(
        "👨‍👩‍👧 Семейный бюджет\n\n"
        "Создать:\n/family_create\n\n"
        "Присоединиться:\n/family_join КОД\n\n"
        "Ввод операций:\nf -40 продукты\nf +1000 зарплата\n\n"
        "Статистика:\n/family_stats\n\n"
        "История:\n/family_history\n\n"
        "Категории:\n/family_categories"
    )
