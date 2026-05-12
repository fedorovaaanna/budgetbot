import aiosqlite
from config import DB_PATH
from utils import now_local, current_year_month
from services.categories import detect_personal_category
from services.family import get_user_family, detect_family_category


async def save_personal_transaction(user_id: int, data: dict):
    year, month = current_year_month()
    category_id, category_name, cleaned_comment = await detect_personal_category(user_id, data["type"], data["comment"])

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO transactions (
            user_id, category_id, category_name_snapshot,
            amount, type, comment, is_extra, year, month, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, category_id, category_name, data["amount"], data["type"],
            cleaned_comment, data["is_extra"], year, month, now_local().isoformat(),
        ))
        await db.commit()
    return category_name, cleaned_comment


async def save_family_transaction(user_id: int, data: dict):
    family = await get_user_family(user_id)
    if not family:
        return None, None, "no_family"

    family_id, _, _, member_number, _ = family
    year, month = current_year_month()
    category_id, category_name, cleaned_comment = await detect_family_category(family_id, data["type"], data["comment"])

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO family_transactions (
            family_id, created_by_user_id, created_by_member_number,
            category_id, category_name_snapshot,
            amount, type, comment, is_extra, year, month, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            family_id, user_id, member_number, category_id, category_name,
            data["amount"], data["type"], cleaned_comment, data["is_extra"],
            year, month, now_local().isoformat(),
        ))
        await db.commit()
    return category_name, cleaned_comment, None
