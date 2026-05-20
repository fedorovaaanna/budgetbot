import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'trial',
            trial_ends_at TEXT,
            paid_at TEXT,
            created_at TEXT NOT NULL
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_map (
            telegram_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            notifications_enabled INTEGER DEFAULT 1,
            family_notifications_enabled INTEGER DEFAULT 1,
            morning_time TEXT DEFAULT '09:00',
            evening_time TEXT DEFAULT '21:00'
        )
        """)

        cur = await db.execute("PRAGMA table_info(user_settings)")
        user_settings_cols = {row[1] for row in await cur.fetchall()}
        if "piggy_bank_start_balance" not in user_settings_cols:
            await db.execute("ALTER TABLE user_settings ADD COLUMN piggy_bank_start_balance REAL DEFAULT 0")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            aliases TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            category_name_snapshot TEXT,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            comment TEXT DEFAULT '',
            is_extra INTEGER DEFAULT 0,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS monthly_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            income_total REAL DEFAULT 0,
            expense_total REAL DEFAULT 0,
            extra_income_total REAL DEFAULT 0,
            extra_expense_total REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            category_summary_json TEXT DEFAULT '{}',
            created_at TEXT,
            UNIQUE(user_id, year, month)
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id INTEGER NOT NULL,
            invite_code TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS family_settings (
            family_id INTEGER PRIMARY KEY,
            piggy_bank_start_balance REAL DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            member_number INTEGER NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(family_id, user_id)
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS family_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            aliases TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS family_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            created_by_user_id INTEGER NOT NULL,
            created_by_member_number INTEGER NOT NULL,
            category_id INTEGER,
            category_name_snapshot TEXT,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            comment TEXT DEFAULT '',
            is_extra INTEGER DEFAULT 0,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS family_monthly_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            income_total REAL DEFAULT 0,
            expense_total REAL DEFAULT 0,
            extra_income_total REAL DEFAULT 0,
            extra_expense_total REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            category_summary_json TEXT DEFAULT '{}',
            created_at TEXT,
            UNIQUE(family_id, year, month)
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS daily_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            user_id INTEGER,
            family_id INTEGER,
            date TEXT NOT NULL,
            morning_balance REAL DEFAULT 0,
            morning_days_left INTEGER DEFAULT 0,
            morning_daily_budget REAL DEFAULT 0,
            created_at TEXT,
            UNIQUE(scope, user_id, family_id, date)
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS notification_sends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_user_id INTEGER NOT NULL,
            scope TEXT NOT NULL,
            family_id INTEGER,
            date TEXT NOT NULL,
            kind TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            UNIQUE(recipient_user_id, scope, family_id, date, kind)
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT,
            currency TEXT,
            amount INTEGER,
            payload TEXT,
            telegram_payment_charge_id TEXT,
            provider_payment_charge_id TEXT,
            created_at TEXT
        )
        """)

        await db.commit()
