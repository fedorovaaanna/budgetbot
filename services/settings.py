import aiosqlite
from config import DB_PATH


async def get_user_settings(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        await db.commit()
        cur = await db.execute("""
        SELECT notifications_enabled, family_notifications_enabled, morning_time, evening_time
        FROM user_settings
        WHERE user_id = ?
        """, (user_id,))
        return await cur.fetchone()


async def set_notifications(user_id: int, enabled: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        await db.execute("UPDATE user_settings SET notifications_enabled = ? WHERE user_id = ?", (enabled, user_id))
        await db.commit()


async def set_family_notifications(user_id: int, enabled: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        await db.execute("UPDATE user_settings SET family_notifications_enabled = ? WHERE user_id = ?", (enabled, user_id))
        await db.commit()


async def set_notify_time(user_id: int, morning: str, evening: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE user_settings SET morning_time = ?, evening_time = ? WHERE user_id = ?", (morning, evening, user_id))
        await db.commit()


async def get_user_piggy_start_balance(user_id: int) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        await db.commit()
        cur = await db.execute("""
        SELECT piggy_bank_start_balance
        FROM user_settings
        WHERE user_id = ?
        """, (user_id,))
        row = await cur.fetchone()
        return float(row[0] or 0)


async def set_user_piggy_start_balance(user_id: int, value: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        await db.execute(
            "UPDATE user_settings SET piggy_bank_start_balance = ? WHERE user_id = ?",
            (value, user_id),
        )
        await db.commit()


async def get_family_piggy_start_balance(family_id: int) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO family_settings (family_id) VALUES (?)", (family_id,))
        await db.commit()
        cur = await db.execute("""
        SELECT piggy_bank_start_balance
        FROM family_settings
        WHERE family_id = ?
        """, (family_id,))
        row = await cur.fetchone()
        return float(row[0] or 0)


async def set_family_piggy_start_balance(family_id: int, value: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO family_settings (family_id) VALUES (?)", (family_id,))
        await db.execute(
            "UPDATE family_settings SET piggy_bank_start_balance = ? WHERE family_id = ?",
            (value, family_id),
        )
        await db.commit()
