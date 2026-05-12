from datetime import datetime
import aiosqlite
from config import DB_PATH, TZ
from utils import current_year_month, days_left_in_month, month_key, money


async def get_personal_stats(user_id: int):
    year, month = current_year_month()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT type, is_extra, category_name_snapshot, SUM(amount)
        FROM transactions
        WHERE user_id = ? AND year = ? AND month = ?
        GROUP BY type, is_extra, category_name_snapshot
        """, (user_id, year, month))
        rows = await cur.fetchall()

        cur = await db.execute("""
        SELECT year, month, income_total, expense_total,
               extra_income_total, extra_expense_total, balance
        FROM monthly_summaries
        WHERE user_id = ?
        ORDER BY year DESC, month DESC
        LIMIT 12
        """, (user_id,))
        old_rows = await cur.fetchall()

    return build_stats_dict(year, month, rows, old_rows)


async def get_family_stats(family_id: int):
    year, month = current_year_month()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT type, is_extra, category_name_snapshot, SUM(amount)
        FROM family_transactions
        WHERE family_id = ? AND year = ? AND month = ?
        GROUP BY type, is_extra, category_name_snapshot
        """, (family_id, year, month))
        rows = await cur.fetchall()

        cur = await db.execute("""
        SELECT year, month, income_total, expense_total,
               extra_income_total, extra_expense_total, balance
        FROM family_monthly_summaries
        WHERE family_id = ?
        ORDER BY year DESC, month DESC
        LIMIT 12
        """, (family_id,))
        old_rows = await cur.fetchall()

    return build_stats_dict(year, month, rows, old_rows)


def build_stats_dict(year: int, month: int, rows, old_rows):
    result = {
        "year": year,
        "month": month,
        "income": 0,
        "expense": 0,
        "extra_income": 0,
        "extra_expense": 0,
        "income_by_category": {},
        "expense_by_category": {},
        "old_months": old_rows,
    }

    for type_, is_extra, category, amount in rows:
        amount = amount or 0
        category = category or "иное"

        if type_ == "income":
            if is_extra:
                result["extra_income"] += amount
            else:
                result["income"] += amount
            result["income_by_category"][category] = result["income_by_category"].get(category, 0) + amount

        elif type_ == "expense":
            if is_extra:
                result["extra_expense"] += amount
            else:
                result["expense"] += amount
            result["expense_by_category"][category] = result["expense_by_category"].get(category, 0) + amount

    return result


def stats_balance(stats: dict):
    return stats["income"] + stats["extra_income"] - stats["expense"] - stats["extra_expense"]


def daily_budget(stats: dict):
    return stats_balance(stats) / days_left_in_month()


def format_stats(stats: dict, title_prefix: str = "Личный бюджет"):
    title = month_key(stats["year"], stats["month"])
    balance = stats_balance(stats)
    days_left = days_left_in_month()
    budget_day = daily_budget(stats)

    text = (
        f"📊 {title_prefix}: {title}\n\n"
        f"Доходы в рамках бюджета: {money(stats['income'])}\n"
        f"Расходы в рамках бюджета: {money(stats['expense'])}\n"
        f"Внебюджетные доходы: {money(stats['extra_income'])}\n"
        f"Внебюджетные расходы: {money(stats['extra_expense'])}\n\n"
        f"Доступно сейчас: {money(balance)}\n"
        f"Дней до конца месяца: {days_left}\n"
        f"Бюджет на день: {money(budget_day)}\n\n"
        f"Расчет: все внесенные доходы минус все внесенные расходы, "
        f"делим на оставшиеся календарные дни месяца, включая сегодня.\n"
    )

    if stats["expense_by_category"]:
        text += "\nРасходы по категориям:\n"
        for category, amount in sorted(stats["expense_by_category"].items()):
            text += f"• {category}: {money(amount)}\n"

    if stats["income_by_category"]:
        text += "\nДоходы по категориям:\n"
        for category, amount in sorted(stats["income_by_category"].items()):
            text += f"• {category}: {money(amount)}\n"

    if stats["old_months"]:
        text += "\nСтарые месяцы, агрегировано:\n"
        for year, month, income, expense, extra_income, extra_expense, old_balance in stats["old_months"][:6]:
            text += (
                f"• {month_key(year, month)}: "
                f"доход {money(income + extra_income)}, "
                f"расход {money(expense + extra_expense)}, "
                f"итог {money(old_balance)}\n"
            )
    return text


async def personal_spent_today(user_id: int):
    start = datetime.combine(datetime.now(TZ).date(), datetime.min.time(), tzinfo=TZ).isoformat()
    end = datetime.combine(datetime.now(TZ).date(), datetime.max.time(), tzinfo=TZ).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND created_at BETWEEN ? AND ?
        """, (user_id, start, end))
        row = await cur.fetchone()
        return row[0] or 0


async def family_spent_today(family_id: int):
    start = datetime.combine(datetime.now(TZ).date(), datetime.min.time(), tzinfo=TZ).isoformat()
    end = datetime.combine(datetime.now(TZ).date(), datetime.max.time(), tzinfo=TZ).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT SUM(amount)
        FROM family_transactions
        WHERE family_id = ? AND type = 'expense' AND created_at BETWEEN ? AND ?
        """, (family_id, start, end))
        row = await cur.fetchone()
        return row[0] or 0
