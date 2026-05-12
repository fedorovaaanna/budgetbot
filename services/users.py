from datetime import timedelta, datetime
import aiosqlite
from config import DB_PATH
from utils import now_local


async def get_internal_user_id(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id FROM user_map WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cur.fetchone()

        if row:
            user_id = row[0]
            await db.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
            await db.commit()
            return user_id

        now = now_local()
        trial_ends = now + timedelta(days=3)

        cur = await db.execute("""
            INSERT INTO users (status, trial_ends_at, created_at)
            VALUES ('trial', ?, ?)
        """, (trial_ends.isoformat(), now.isoformat()))

        user_id = cur.lastrowid

        await db.execute("INSERT INTO user_map (telegram_id, user_id) VALUES (?, ?)", (telegram_id, user_id))
        await db.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        await db.commit()
        return user_id


async def get_telegram_id_by_user_id(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT telegram_id FROM user_map WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else None


async def get_user_status(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT status, trial_ends_at, paid_at FROM users WHERE id = ?", (user_id,))
        return await cur.fetchone()


async def has_access(user_id: int) -> bool:
    row = await get_user_status(user_id)
    if not row:
        return False

    status, trial_ends_at, _ = row

    if status == "paid":
        return True

    if status == "trial" and trial_ends_at:
        if datetime.fromisoformat(trial_ends_at) > now_local():
            return True

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET status = 'expired' WHERE id = ?", (user_id,))
            await db.commit()

    return False


async def activate_paid(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET status = 'paid', paid_at = ? WHERE id = ?", (now_local().isoformat(), user_id))
        await db.commit()


async def save_payment(user_id: int, payment):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO payments (
                user_id, provider, currency, amount, payload,
                telegram_payment_charge_id, provider_payment_charge_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "telegram_stars",
            payment.currency,
            payment.total_amount,
            payment.invoice_payload,
            payment.telegram_payment_charge_id,
            payment.provider_payment_charge_id,
            now_local().isoformat(),
        ))
        await db.commit()
