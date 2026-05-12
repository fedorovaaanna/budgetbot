import re
import calendar
from datetime import datetime
from config import TZ, RETENTION_MONTHS


def now_local() -> datetime:
    return datetime.now(TZ)


def today_str() -> str:
    return now_local().date().isoformat()


def current_year_month() -> tuple[int, int]:
    n = now_local()
    return n.year, n.month


def month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def days_left_in_month() -> int:
    today = now_local()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return max(last_day - today.day + 1, 1)


def cutoff_year_month() -> tuple[int, int]:
    today = now_local()
    year = today.year
    month = today.month - (RETENTION_MONTHS - 1)
    while month <= 0:
        month += 12
        year -= 1
    return year, month


def money(value) -> str:
    value = value or 0
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def parse_amount(raw: str):
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def valid_time(value: str) -> bool:
    return bool(re.match(r"^\d{2}:\d{2}$", value.strip()))


def tx_sign(type_: str, is_extra: int) -> str:
    if type_ == "income":
        return "++" if is_extra else "+"
    return "--" if is_extra else "-"
