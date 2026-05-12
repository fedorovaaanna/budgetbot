import random
import string
import aiosqlite
from config import DB_PATH
from utils import now_local
from parser import category_match


def generate_invite_code() -> str:
    suffix = "".join(random.choices(string.digits, k=5))
    return f"FAM-{suffix}"


async def get_user_family(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT f.id, f.owner_user_id, f.invite_code, fm.member_number, fm.role
        FROM family_members fm
        JOIN families f ON f.id = fm.family_id
        WHERE fm.user_id = ? AND f.is_active = 1
        ORDER BY f.id DESC
        LIMIT 1
        """, (user_id,))
        return await cur.fetchone()


async def create_family(user_id: int):
    existing = await get_user_family(user_id)
    if existing:
        return existing[0], existing[2], False

    async with aiosqlite.connect(DB_PATH) as db:
        invite_code = generate_invite_code()
        cur = await db.execute("""
        INSERT INTO families (owner_user_id, invite_code, is_active, created_at)
        VALUES (?, ?, 1, ?)
        """, (user_id, invite_code, now_local().isoformat()))
        family_id = cur.lastrowid
        await db.execute("""
        INSERT INTO family_members (family_id, user_id, member_number, role, created_at)
        VALUES (?, ?, 1, 'owner', ?)
        """, (family_id, user_id, now_local().isoformat()))
        await db.commit()
    return family_id, invite_code, True


async def join_family(user_id: int, invite_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM families WHERE invite_code = ? AND is_active = 1", (invite_code.strip(),))
        row = await cur.fetchone()
        if not row:
            return None, "not_found"

        family_id = row[0]
        cur = await db.execute("SELECT COUNT(*) FROM family_members WHERE family_id = ?", (family_id,))
        count = (await cur.fetchone())[0]

        if count >= 2:
            return family_id, "full"

        cur = await db.execute("SELECT id FROM family_members WHERE family_id = ? AND user_id = ?", (family_id, user_id))
        exists = await cur.fetchone()
        if exists:
            return family_id, "already"

        await db.execute("""
        INSERT INTO family_members (family_id, user_id, member_number, role, created_at)
        VALUES (?, ?, ?, 'member', ?)
        """, (family_id, user_id, count + 1, now_local().isoformat()))
        await db.commit()
    return family_id, "joined"


async def get_family_members(family_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT user_id, member_number, role
        FROM family_members
        WHERE family_id = ?
        ORDER BY member_number
        """, (family_id,))
        return await cur.fetchall()


async def add_family_category(family_id: int, type_: str, name: str, aliases: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO family_categories (family_id, type, name, aliases, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """, (family_id, type_, name, aliases, now_local().isoformat(), now_local().isoformat()))
        await db.commit()


async def get_family_categories(family_id: int, type_: str | None = None, active_only: bool = True):
    query = "SELECT id, type, name, aliases, is_active FROM family_categories WHERE family_id = ?"
    params = [family_id]

    if type_:
        query += " AND type = ?"
        params.append(type_)

    if active_only:
        query += " AND is_active = 1"

    query += " ORDER BY type, id"

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(query, params)
        return await cur.fetchall()


async def rename_family_category(family_id: int, category_id: int, new_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        UPDATE family_categories SET name = ?, updated_at = ? WHERE id = ? AND family_id = ?
        """, (new_name, now_local().isoformat(), category_id, family_id))
        await db.commit()
        return cur.rowcount


async def set_family_category_aliases(family_id: int, category_id: int, aliases: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        UPDATE family_categories SET aliases = ?, updated_at = ? WHERE id = ? AND family_id = ?
        """, (aliases, now_local().isoformat(), category_id, family_id))
        await db.commit()
        return cur.rowcount


async def disable_family_category(family_id: int, category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        UPDATE family_categories SET is_active = 0, updated_at = ? WHERE id = ? AND family_id = ?
        """, (now_local().isoformat(), category_id, family_id))
        await db.commit()
        return cur.rowcount


async def detect_family_category(family_id: int, type_: str, comment: str):
    categories = await get_family_categories(family_id, type_)
    for cid, _, name, aliases, _ in categories:
        ok, cleaned = category_match(comment, name, aliases)
        if ok:
            return cid, name, cleaned
    return None, "иное", comment
