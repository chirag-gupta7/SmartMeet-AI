"""Regression tests for timezone handling in the voice/natural-language
scheduling path.

The bug: parse_natural_language_datetime() built dates from the server's
naive local clock, and calendar_event_parser labeled that wall time as
'UTC'. On a server in a non-UTC timezone, "tomorrow at 3pm" was created
as 3pm UTC instead of 3pm in the user's timezone.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

import app.services.datetime_parser as datetime_parser
from app.services.calendar_event_parser import create_event_manual_parse
from app.services.command_processor import VoiceCommandProcessor


def _frozen_now_class(fixed_utc):
    """datetime replacement whose .now() always returns fixed_utc."""

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: D102
            aware = fixed_utc if fixed_utc.tzinfo else fixed_utc.replace(tzinfo=ZoneInfo("UTC"))
            return aware.astimezone(tz) if tz else aware

    return _FrozenDatetime


# Saturday 2026-08-22 10:00 UTC == 15:30 Asia/Kolkata.
FIXED_NOW = datetime(2026, 8, 22, 10, 0, 0, tzinfo=ZoneInfo("UTC"))


@pytest.fixture()
def frozen_clock(monkeypatch):
    monkeypatch.setattr(datetime_parser, "datetime", _frozen_now_class(FIXED_NOW))


@pytest.fixture()
def mock_calendar_service():
    service = MagicMock()
    service.events().insert.return_value.execute.return_value = {"id": "evt-123"}
    return service


# --- parse_natural_language_datetime --------------------------------------


def test_parse_anchors_relative_dates_to_requested_timezone():
    result = datetime_parser.parse_natural_language_datetime(
        "Schedule a meeting tomorrow at 3pm", "Asia/Kolkata"
    )

    assert result["success"] is True
    assert result["timezone"] == "Asia/Kolkata"
    start = result["start_datetime"]
    assert start.tzinfo is not None
    assert start.utcoffset().total_seconds() == 5.5 * 3600
    # 3pm stays 3pm in the user's wall clock...
    assert (start.hour, start.minute) == (15, 0)
    # ...and 'tomorrow' is tomorrow *in Kolkata*, not on the server.


def test_parse_converts_explicit_dates_from_naive_dateutil_results():
    result = datetime_parser.parse_natural_language_datetime(
        "Meeting on August 25 at 9am", "America/New_York"
    )
    start = result["start_datetime"]
    assert start.tzinfo is not None
    assert (start.month, start.day) == (8, 25)
    assert (start.hour, start.minute) == (9, 0)


def test_unknown_timezone_falls_back_to_utc():
    result = datetime_parser.parse_natural_language_datetime("tomorrow at 9am", "Not/AZone")
    assert result["timezone"] == "UTC"
    assert result["start_datetime"].utcoffset().total_seconds() == 0


# --- Google payload construction (the actual regression) -------------------


def test_voice_event_payload_represents_intended_local_time(
    frozen_clock, mock_calendar_service
):
    """A Kolkata user saying 'tomorrow at 3pm' must get 3pm IST on their
    calendar - i.e. 09:30 UTC - regardless of where the server runs."""
    ist = ZoneInfo("Asia/Kolkata")

    result = create_event_manual_parse(
        "Schedule a design review tomorrow at 3pm",
        lambda: mock_calendar_service,
        timezone_name="Asia/Kolkata",
    )

    assert result["success"], result.get("error")
    body = mock_calendar_service.events().insert.call_args.kwargs["body"]

    assert body["start"]["timeZone"] == "Asia/Kolkata"
    assert body["end"]["timeZone"] == "Asia/Kolkata"

    sent_start = datetime.fromisoformat(body["start"]["dateTime"])
    sent_end = datetime.fromisoformat(body["end"]["dateTime"])

    intended_local_start = datetime(2026, 8, 23, 15, 0, tzinfo=ist)
    intended_local_end = intended_local_start + timedelta(hours=1)
    assert sent_start.astimezone(ist) == intended_local_start
    assert sent_end.astimezone(ist) == intended_local_end

    # dateTime itself must carry the correct instant as ISO8601 w/ offset.
    assert body["start"]["dateTime"] == "2026-08-23T09:30:00+00:00"
    assert body["end"]["dateTime"] == "2026-08-23T10:30:00+00:00"


def test_default_timezone_is_utc_not_server_local(frozen_clock, mock_calendar_service):
    """Without a stored user timezone the payload must be plain UTC -
    never the server's own local clock mislabeled as anything."""
    result = create_event_manual_parse(
        "Schedule a design review tomorrow at 3pm",
        lambda: mock_calendar_service,
    )

    assert result["success"], result.get("error")
    body = mock_calendar_service.events().insert.call_args.kwargs["body"]

    assert body["start"]["timeZone"] == "UTC"
    assert body["start"]["dateTime"] == "2026-08-23T15:00:00+00:00"


def test_all_day_events_use_plain_dates_regardless_of_timezone(
    frozen_clock, mock_calendar_service
):
    result = create_event_manual_parse(
        "Schedule an all-day offsite tomorrow",
        lambda: mock_calendar_service,
        timezone_name="Asia/Kolkata",
    )

    assert result["success"], result.get("error")
    body = mock_calendar_service.events().insert.call_args.kwargs["body"]
    assert body["start"]["date"] == "2026-08-23"
    assert body["end"]["date"] == "2026-08-24"


# --- threading through the call chain ---------------------------------------


def test_processor_passes_user_timezone_to_quick_event_creator(app, user_factory):
    user = user_factory()
    captured = {}

    def fake_create(user_id, text, timezone_name=None):
        captured["user_id"] = user_id
        captured["text"] = text
        captured["timezone_name"] = timezone_name
        return {
            "success": True,
            "event": {"summary": "Lunch", "date": "August 23, 2026"},
            "message": "Event created: 'Lunch'",
        }

    with patch(
        "app.services.google_calendar.create_quick_event_for_user", side_effect=fake_create
    ):
        result = VoiceCommandProcessor(
            user_id=user.id, timezone_name="Asia/Kolkata"
        ).create_calendar_event("Schedule lunch tomorrow at noon")

    assert result["success"] is True
    assert captured["user_id"] == user.id
    assert captured["timezone_name"] == "Asia/Kolkata"


# --- User.timezone API -------------------------------------------------------


def test_user_defaults_to_utc_and_exposes_timezone(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "TZ Default", "email": "tzdefault@example.com", "password": "password123"},
    )
    assert resp.status_code in (200, 201)
    assert resp.get_json()["user"]["timezone"] == "UTC"


def test_patch_me_updates_and_validates_timezone(client, user_factory, auth_headers):
    user = user_factory(email="tzpatch@example.com")
    headers = auth_headers(user.id)

    resp = client.patch("/api/auth/me", json={"timezone": "Asia/Kolkata"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["user"]["timezone"] == "Asia/Kolkata"

    me = client.get("/api/auth/me", headers=headers)
    assert me.get_json()["user"]["timezone"] == "Asia/Kolkata"

    bad = client.patch("/api/auth/me", json={"timezone": "Mars/Olympus"}, headers=headers)
    assert bad.status_code == 400

    # Existing value survives a rejected update.
    still = client.get("/api/auth/me", headers=headers)
    assert still.get_json()["user"]["timezone"] == "Asia/Kolkata"
