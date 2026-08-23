"""Regression: find_free_time computed 9-17 business hours in UTC, ignoring
the user's stored timezone. The freebusy window must be built in the
user's local timezone."""
from datetime import datetime
from unittest.mock import patch

from app.services.command_processor import VoiceCommandProcessor


def test_find_free_time_uses_user_timezone_for_business_hours(app, user_factory):
    user = user_factory(email="freetime-tz@example.com")
    captured = {}

    def fake_freebusy(user_id, start, end):
        captured["start"] = start
        captured["end"] = end
        return []

    processor = VoiceCommandProcessor(user_id=user.id, timezone_name="Asia/Kolkata")

    with patch(
        "app.services.google_calendar.query_freebusy_for_user",
        side_effect=fake_freebusy,
    ):
        result = processor.find_free_time()

    assert result["success"] is True
    assert captured["start"].utcoffset().total_seconds() == 5.5 * 3600
    assert (captured["start"].hour, captured["start"].minute) == (9, 0)
    assert (captured["end"].hour, captured["end"].minute) == (17, 0)


def test_find_free_time_defaults_to_utc_without_timezone(app, user_factory):
    user = user_factory(email="freetime-utc@example.com")
    captured = {}

    def fake_freebusy(user_id, start, end):
        captured["start"] = start
        captured["end"] = end
        return []

    processor = VoiceCommandProcessor(user_id=user.id)

    with patch(
        "app.services.google_calendar.query_freebusy_for_user",
        side_effect=fake_freebusy,
    ):
        processor.find_free_time()

    assert captured["start"].utcoffset().total_seconds() == 0
