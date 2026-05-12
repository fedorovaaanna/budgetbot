import aiosqlite
from config import DB_PATH


async def get_personal_history(user_id: int, limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT type, is_extra, amount, category_name_snapshot, comment, created_at
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (user_id, limit))
        return await cur.fetchall()


async def get_family_history(family_id: int, limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT created_by_member_number, type, is_extra, amount, category_name_snapshot, comment, created_at
        FROM family_transactions
        WHERE family_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (family_id, limit))
        return await cur.fetchall()
