import re
from utils import parse_amount


def normalize_signs(text: str) -> str:
    """
    Нормализует разные виды тире с телефона.

    Поддерживает:
    --100 больница
    —100 больница
    –100 больница
    −100 больница
    """
    text = text.strip()

    if text.startswith("++") or text.startswith("--"):
        return text

    if text.startswith("—") or text.startswith("–") or text.startswith("−"):
        return "--" + text[1:].strip()

    return text


def split_family_prefix(text: str):
    """
    f -40 продукты => family=True, -40 продукты
    ф -40 продукты => family=True
    семья -40 продукты => family=True
    """
    text = text.strip()
    lowered = text.lower()

    prefixes = ["f ", "ф ", "family ", "семья "]

    for prefix in prefixes:
        if lowered.startswith(prefix):
            return True, text[len(prefix):].strip()

    return False, text


def parse_transaction(text: str):
    is_family, text = split_family_prefix(text)
    text = normalize_signs(text)

    pattern = r"^(\+\+|\+|--|-)\s*(\d+(?:[.,]\d+)?)\s*(.*)$"
    match = re.match(pattern, text.strip())

    if not match:
        return None

    sign, amount_raw, comment = match.groups()
    amount = parse_amount(amount_raw)

    if amount is None:
        return None

    type_ = "income" if sign in ["+", "++"] else "expense"
    is_extra = 1 if sign in ["++", "--"] else 0

    return {
        "scope": "family" if is_family else "personal",
        "amount": amount,
        "type": type_,
        "is_extra": is_extra,
        "comment": comment.strip(),
    }


def parse_category_line(text: str):
    parts = text.strip().split("|", 1)
    name = parts[0].strip()
    aliases = ""

    if len(parts) == 2:
        aliases = parts[1].strip()

    if not name:
        return None

    return name, aliases


def category_match(comment: str, category_name: str, aliases: str):
    comment_norm = comment.lower().strip()
    variants = [category_name]

    if aliases:
        variants += [a.strip() for a in aliases.split(",") if a.strip()]

    for variant in variants:
        variant_norm = variant.lower().strip()
        if not variant_norm:
            continue

        if comment_norm == variant_norm:
            return True, ""

        if comment_norm.startswith(variant_norm + " "):
            return True, comment[len(variant):].strip()

    return False, comment
