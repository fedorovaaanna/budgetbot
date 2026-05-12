import json
import aiosqlite
from config import DB_PATH
from utils import cutoff_year_month, now_local


async def cleanup_old_transactions():
    cutoff_year, cutoff_month = cutoff_year_month()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT DISTINCT user_id, year, month
        FROM transactions
        WHERE year < ? OR (year = ? AND month < ?)
        """, (cutoff_year, cutoff_year, cutoff_month))
        personal_months = await cur.fetchall()

        cur = await db.execute("""
        SELECT DISTINCT family_id, year, month
        FROM family_transactions
        WHERE year < ? OR (year = ? AND month < ?)
        """, (cutoff_year, cutoff_year, cutoff_month))
        family_months = await cur.fetchall()

    for user_id, year, month in personal_months:
        await summarize_and_delete_personal_month(user_id, year, month)

    for family_id, year, month in family_months:
        await summarize_and_delete_family_month(family_id, year, month)


async def summarize_rows(rows):
    income_total = 0
    expense_total = 0
    extra_income_total = 0
    extra_expense_total = 0
    category_summary = {}

    for type_, is_extra, category, amount in rows:
        amount = amount or 0
        category = category or "иное"
        category_summary.setdefault(category, {"income": 0, "expense": 0, "extra_income": 0, "extra_expense": 0})

        if type_ == "income" and is_extra:
            extra_income_total += amount
            category_summary[category]["extra_income"] += amount
        elif type_ == "income":
            income_total += amount
            category_summary[category]["income"] += amount
        elif type_ == "expense" and is_extra:
            extra_expense_total += amount
            category_summary[category]["extra_expense"] += amount
        elif type_ == "expense":
            expense_total += amount
            category_summary[category]["expense"] += amount

    balance = income_total + extra_income_total - expense_total - extra_expense_total
    return income_total, expense_total, extra_income_total, extra_expense_total, balance, category_summary


async def summarize_and_delete_personal_month(user_id: int, year: int, month: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT type, is_extra, category_name_snapshot, SUM(amount)
        FROM transactions
        WHERE user_id = ? AND year = ? AND month = ?
        GROUP BY type, is_extra, category_name_snapshot
        """, (user_id, year, month))
        rows = await cur.fetchall()
        if not rows:
            return
        income, expense, extra_income, extra_expense, balance, category_summary = await summarize_rows(rows)
        await db.execute("""
        INSERT INTO monthly_summaries (
            user_id, year, month, income_total, expense_total,
            extra_income_total, extra_expense_total, balance,
            category_summary_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, year, month)
        DO UPDATE SET
            income_total = excluded.income_total,
            expense_total = excluded.expense_total,
            extra_income_total = excluded.extra_income_total,
            extra_expense_total = excluded.extra_expense_total,
            balance = excluded.balance,
            category_summary_json = excluded.category_summary_json
        """, (user_id, year, month, income, expense, extra_income, extra_expense, balance, json.dumps(category_summary, ensure_ascii=False), now_local().isoformat()))
        await db.execute("DELETE FROM transactions WHERE user_id = ? AND year = ? AND month = ?", (user_id, year, month))
        await db.commit()


async def summarize_and_delete_family_month(family_id: int, year: int, month: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT type, is_extra, category_name_snapshot, SUM(amount)
        FROM family_transactions
        WHERE family_id = ? AND year = ? AND month = ?
        GROUP BY type, is_extra, category_name_snapshot
        """, (family_id, year, month))
        rows = await cur.fetchall()
        if not rows:
            return
        income, expense, extra_income, extra_expense, balance, category_summary = await summarize_rows(rows)
        await db.execute("""
        INSERT INTO family_monthly_summaries (
            family_id, year, month, income_total, expense_total,
            extra_income_total, extra_expense_total, balance,
            category_summary_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(family_id, year, month)
        DO UPDATE SET
            income_total = excluded.income_total,
            expense_total = excluded.expense_total,
            extra_income_total = excluded.extra_income_total,
            extra_expense_total = excluded.extra_expense_total,
            balance = excluded.balance,
            category_summary_json = excluded.category_summary_json
        """, (family_id, year, month, income, expense, extra_income, extra_expense, balance, json.dumps(category_summary, ensure_ascii=False), now_local().isoformat()))
        await db.execute("DELETE FROM family_transactions WHERE family_id = ? AND year = ? AND month = ?", (family_id, year, month))
        await db.commit()
