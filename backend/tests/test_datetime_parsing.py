from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

from app.services.datetime_parser import parse_natural_language_datetime
from app.services.calendar_event_parser import create_event_manual_parse


UTC = "UTC"


def _next_weekday(base, target_weekday, offset):
    days_ahead = (target_weekday - base.weekday()) % 7 or 7
    return base + timedelta(days=days_ahead)


def test_tomorrow_at_3pm_parses_successfully():
    result = parse_natural_language_datetime("Schedule a meeting tomorrow at 3pm", UTC)

    assert result["success"] is True
    assert result["is_all_day"] is False
    assert "start_datetime" in result
    assert result["start_datetime"].hour == 15
    assert result["start_datetime"].minute == 0
    assert result["end_datetime"] == result["start_datetime"] + timedelta(hours=1)

    expected_day = datetime.now(ZoneInfo(UTC)) + timedelta(days=1)
    assert result["start_datetime"].date() == expected_day.date()


def test_day_keyword_without_time_is_all_day():
    result = parse_natural_language_datetime("team offsite next Friday", UTC)
    now = datetime.now(ZoneInfo(UTC))

    assert result["success"] is True
    assert result["is_all_day"] is True
    assert "start_date" in result
    assert "start_datetime" not in result

    # Next Friday relative to now (weekday 4), matching parser logic.
    days_ahead = (11 - now.weekday()) % 7 or 7
    assert result["start_date"] == (now + timedelta(days=days_ahead)).date()


def test_garbage_input_returns_failure():
    result = parse_natural_language_datetime("schedule blah", UTC)

    assert result["success"] is False
    assert "error" in result
    assert result["error"]
    assert "start_datetime" not in result
    assert "start_date" not in result


def test_manual_parse_reports_error_for_garbage_input():
    def _unexpected_service():
        raise AssertionError("calendar service must not be created for unparseable input")

    result = create_event_manual_parse(
        "schedule blah", _unexpected_service, UTC
    )

    assert result["success"] is False
    assert result["error"] == "Could not understand the date and time for this event"
    assert "Could not understand when this event should be scheduled" in result["message"]
