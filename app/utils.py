"""Small display helpers shared by the UI."""

from __future__ import annotations

from datetime import date, datetime


def format_file_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "—"
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def format_date(iso_date: str, short: bool = False) -> str:
    """Format an ISO date for readable UI display."""
    try:
        value = date.fromisoformat(iso_date)
    except (ValueError, TypeError):
        return iso_date or "—"
    if short:
        return value.strftime("%d %b")
    return value.strftime("%d %b %Y")


def today_iso() -> str:
    return date.today().isoformat()


def now_time_label() -> str:
    return datetime.now().strftime("%H:%M")


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural or singular + 's'}"
