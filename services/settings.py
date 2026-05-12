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
