"""Datetime helpers shared by the API routes."""
from datetime import datetime, timezone


def to_naive_utc(value: datetime) -> datetime:
    """Normalize a parsed datetime to the app's storage convention: naive UTC.

    Clients may send ISO8601 strings with ``Z`` or explicit offsets; storing
    those as-is mixes aware and naive values in the same column, which breaks
    ordering/comparison (silently on SQLite, loudly on PostgreSQL).
    """
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
