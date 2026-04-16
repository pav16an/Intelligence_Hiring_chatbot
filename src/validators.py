from __future__ import annotations

import re

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[0-9][0-9\-\s()]{7,16}[0-9]$")


def sanitize_text(text: str) -> str:
    return " ".join(text.strip().split())


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone.strip()))


def parse_years_of_experience(raw_value: str) -> float | None:
    value = raw_value.strip().replace("+", "")
    try:
        years = float(value)
    except ValueError:
        return None
    if years < 0 or years > 60:
        return None
    return years


def parse_csv_list(raw_value: str) -> list[str]:
    parts = [sanitize_text(item) for item in raw_value.split(",")]
    return [item for item in parts if item]


def normalize_tech_stack(raw_value: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in parse_csv_list(raw_value):
        key = item.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(item)
    return ordered
