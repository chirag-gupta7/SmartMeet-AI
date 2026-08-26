"""Datetime helpers shared by the API routes."""
from datetime import datetime, timezone
from dateutil import parser


def parse_iso_datetime(value_str: str) -> datetime:
    """Fast parse ISO8601 datetime strings using native datetime.fromisoformat.

    BOLT OPTIMIZATION: datetime.fromisoformat is ~100x faster than
    dateutil.parser.parse for ISO8601 strings. Fall back to dateutil.parser
    only for non-standard formats.
    """
    if not isinstance(value_str, str):
        raise TypeError("ISO datetime value must be a string")
    clean_str = (
        value_str.replace("Z", "+00:00")
        if value_str.endswith("Z")
        else value_str
    )
    try:
        return datetime.fromisoformat(clean_str)
    except ValueError:
        return parser.parse(value_str)


def to_naive_utc(value: datetime) -> datetime:
    """Normalize a parsed datetime to the app's storage convention: naive UTC.

    Clients may send ISO8601 strings with ``Z`` or explicit offsets; storing
    those as-is mixes aware and naive values in the same column, which breaks
    ordering/comparison (silently on SQLite, loudly on PostgreSQL).
    """
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
