import aiosqlite
from config import DB_PATH
from utils import today_str, now_local, days_left_in_month, money
from services.users import get_telegram_id_by_user_id, has_access
from services.settings import get_user_settings
from services.family import get_user_family
from services.stats import get_personal_stats, get_family_stats, stats_balance, personal_spent_today, family_spent_today


async def already_sent(recipient_user_id: int, scope: str, family_id, kind: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT id FROM notification_sends
        WHERE recipient_user_id = ?
          AND scope = ?
          AND COALESCE(family_id, 0) = COALESCE(?, 0)
          AND date = ?
          AND kind = ?
        """, (recipient_user_id, scope, family_id, today_str(), kind))
        return await cur.fetchone() is not None


async def mark_sent(recipient_user_id: int, scope: str, family_id, kind: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR IGNORE INTO notification_sends
        (recipient_user_id, scope, family_id, date, kind, sent_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (recipient_user_id, scope, family_id, today_str(), kind, now_local().isoformat()))
        await db.commit()


async def get_or_create_daily_snapshot(scope: str, stats: dict, user_id=None, family_id=None):
    balance = stats_balance(stats)
    days_left = days_left_in_month()
    day_budget = balance / days_left
    d = today_str()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR IGNORE INTO daily_snapshots (
            scope, user_id, family_id, date,
            morning_balance, morning_days_left, morning_daily_budget, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (scope, user_id, family_id, d, balance, days_left, day_budget, now_local().isoformat()))

        cur = await db.execute("""
        SELECT morning_balance, morning_days_left, morning_daily_budget
        FROM daily_snapshots
        WHERE scope = ?
          AND COALESCE(user_id, 0) = COALESCE(?, 0)
          AND COALESCE(family_id, 0) = COALESCE(?, 0)
          AND date = ?
        """, (scope, user_id, family_id, d))
        row = await cur.fetchone()
        await db.commit()

    return {
        "morning_balance": row[0],
        "morning_days_left": row[1],
        "morning_daily_budget": row[2],
    }


def format_morning_message(title: str, snapshot: dict):
    return (
        f"☀️ {title}\n\n"
        f"Доступно сейчас: {money(snapshot['morning_balance'])}\n"
        f"Дней до конца месяца: {snapshot['morning_days_left']}\n"
        f"Бюджет на сегодня: {money(snapshot['morning_daily_budget'])}\n\n"
        f"Расчет: доступные деньги / оставшиеся календарные дни месяца, включая сегодня."
    )


def format_evening_message(title: str, snapshot: dict, spent_today: float, current_balance: float):
    day_budget = snapshot["morning_daily_budget"]
    diff = day_budget - spent_today
    tomorrow_days = max(days_left_in_month() - 1, 1)
    tomorrow_budget = current_balance / tomorrow_days

    if diff >= 0:
        result_line = f"Осталось от дневного бюджета: {money(diff)}"
    else:
        result_line = f"Перерасход за день: {money(abs(diff))}"

    return (
        f"🌙 {title}\n\n"
        f"Сегодня потрачено: {money(spent_today)}\n"
        f"Бюджет на день был: {money(day_budget)}\n\n"
        f"{result_line}\n\n"
        f"Доступно до конца месяца: {money(current_balance)}\n"
        f"Новый дневной бюджет с завтра: {money(tomorrow_budget)}"
    )


async def send_daily_notifications(bot):
    current_time = now_local().strftime("%H:%M")

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT us.user_id, us.notifications_enabled, us.family_notifications_enabled,
               us.morning_time, us.evening_time
        FROM user_settings us
        JOIN users u ON u.id = us.user_id
        WHERE u.status IN ('trial', 'paid')
        """)
        users = await cur.fetchall()

    for user_id, personal_enabled, family_enabled, morning_time, evening_time in users:
        telegram_id = await get_telegram_id_by_user_id(user_id)
        if not telegram_id or not await has_access(user_id):
            continue

        if personal_enabled and current_time == morning_time and not await already_sent(user_id, "personal", None, "morning"):
            stats = await get_personal_stats(user_id)
            snapshot = await get_or_create_daily_snapshot("personal", stats, user_id=user_id)
            await bot.send_message(telegram_id, format_morning_message("Личный бюджет", snapshot))
            await mark_sent(user_id, "personal", None, "morning")

        if personal_enabled and current_time == evening_time and not await already_sent(user_id, "personal", None, "evening"):
            stats = await get_personal_stats(user_id)
            snapshot = await get_or_create_daily_snapshot("personal", stats, user_id=user_id)
            spent = await personal_spent_today(user_id)
            await bot.send_message(telegram_id, format_evening_message("Личный итог дня", snapshot, spent, stats_balance(stats)))
            await mark_sent(user_id, "personal", None, "evening")

        family = await get_user_family(user_id)
        if family and family_enabled:
            family_id = family[0]
            if current_time == morning_time and not await already_sent(user_id, "family", family_id, "morning"):
                stats = await get_family_stats(family_id)
                snapshot = await get_or_create_daily_snapshot("family", stats, family_id=family_id)
                await bot.send_message(telegram_id, format_morning_message("Семейный бюджет", snapshot))
                await mark_sent(user_id, "family", family_id, "morning")

            if current_time == evening_time and not await already_sent(user_id, "family", family_id, "evening"):
                stats = await get_family_stats(family_id)
                snapshot = await get_or_create_daily_snapshot("family", stats, family_id=family_id)
                spent = await family_spent_today(family_id)
                await bot.send_message(telegram_id, format_evening_message("Семейный итог дня", snapshot, spent, stats_balance(stats)))
                await mark_sent(user_id, "family", family_id, "evening")
