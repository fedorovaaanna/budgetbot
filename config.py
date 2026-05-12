import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROMO_CODE = os.getenv("PROMO_CODE", "FREEFRIENDS")
LIFETIME_PRICE_STARS = int(os.getenv("LIFETIME_PRICE_STARS", "2500"))

DB_PATH = os.getenv("DB_PATH", "budget.db")
TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tbilisi"))
RETENTION_MONTHS = int(os.getenv("RETENTION_MONTHS", "3"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")
