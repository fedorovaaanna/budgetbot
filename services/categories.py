import aiosqlite
from config import DB_PATH
from utils import now_local
from parser import category_match


async def add_category(user_id: int, type_: str, name: str, aliases: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO categories (user_id, type, name, aliases, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """, (user_id, type_, name, aliases, now_local().isoformat(), now_local().isoformat()))
        await db.commit()


async def get_categories(user_id: int, type_: str | None = None, active_only: bool = True):
    query = "SELECT id, type, name, aliases, is_active FROM categories WHERE user_id = ?"
    params = [user_id]

    if type_:
        query += " AND type = ?"
        params.append(type_)

    if active_only:
        query += " AND is_active = 1"

    query += " ORDER BY type, id"

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(query, params)
        return await cur.fetchall()


async def rename_category(user_id: int, category_id: int, new_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        UPDATE categories SET name = ?, updated_at = ? WHERE id = ? AND user_id = ?
        """, (new_name, now_local().isoformat(), category_id, user_id))
        await db.commit()
        return cur.rowcount


async def set_category_aliases(user_id: int, category_id: int, aliases: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        UPDATE categories SET aliases = ?, updated_at = ? WHERE id = ? AND user_id = ?
        """, (aliases, now_local().isoformat(), category_id, user_id))
        await db.commit()
        return cur.rowcount


async def disable_category(user_id: int, category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        UPDATE categories SET is_active = 0, updated_at = ? WHERE id = ? AND user_id = ?
        """, (now_local().isoformat(), category_id, user_id))
        await db.commit()
        return cur.rowcount


async def detect_personal_category(user_id: int, type_: str, comment: str):
    categories = await get_categories(user_id, type_)
    for cid, _, name, aliases, _ in categories:
        ok, cleaned = category_match(comment, name, aliases)
        if ok:
            return cid, name, cleaned
    return None, "иное", comment
