"""Tests for the per-user Google Calendar credential flow (post-refactor)."""
import json
from unittest.mock import MagicMock, patch

from app.extensions import db
from app.services import google_calendar
from app.services.command_processor import VoiceCommandProcessor


def _raw_event(event_id="evt1", summary="Standup"):
    return {
        "id": event_id,
        "summary": summary,
        "start": {"dateTime": "2026-08-23T09:00:00Z"},
        "end": {"dateTime": "2026-08-23T09:30:00Z"},
        "location": "Zoom",
        "htmlLink": "https://calendar.google.com/evt1",
    }


def _fake_service(items=None):
    service = MagicMock()
    service.events().list.return_value.execute.return_value = {"items": items or []}
    return service


# --- get_service_for_user -------------------------------------------------


def test_get_service_for_user_returns_none_without_credentials(app, user_factory):
    user = user_factory()
    assert google_calendar.get_service_for_user(user.id) is None


def test_get_service_for_user_builds_service_from_stored_creds(app, user_factory):
    user = user_factory()
    stored = {"token": "tok", "refresh_token": "r", "client_id": "c", "client_secret": "s"}
    user.google_credentials = stored
    db.session.commit()

    mock_creds = MagicMock()
    mock_creds.expired = False

    with patch("app.services.google_calendar.Credentials") as mock_creds_cls, patch(
        "app.services.google_calendar.build"
    ) as mock_build:
        mock_creds_cls.from_authorized_user_info.return_value = mock_creds
        service = google_calendar.get_service_for_user(user.id)

    assert service is not None
    mock_creds_cls.from_authorized_user_info.assert_called_once_with(stored)
    mock_build.assert_called_once()


def test_expired_credentials_are_refreshed_and_persisted(app, user_factory):
    user = user_factory()
    user.google_credentials = {
        "token": "old-token",
        "refresh_token": "r",
        "client_id": "c",
        "client_secret": "s",
    }
    db.session.commit()

    mock_creds = MagicMock()
    mock_creds.expired = True
    mock_creds.refresh_token = "r"
    refreshed_json = json.dumps(
        {"token": "brand-new", "refresh_token": "r", "client_id": "c", "client_secret": "s"}
    )
    mock_creds.to_json.return_value = refreshed_json

    with patch("app.services.google_calendar.Credentials") as mock_creds_cls, patch(
        "app.services.google_calendar.build", return_value=_fake_service()
    ):
        mock_creds_cls.from_authorized_user_info.return_value = mock_creds
        google_calendar.get_service_for_user(user.id)

    mock_creds.refresh.assert_called_once()
    assert user.google_credentials == json.loads(refreshed_json)


# --- command processor not-connected contract -----------------------------


def test_processor_reports_not_connected_without_creds(app, user_factory):
    """voice.py surfaces an auth URL when the error mentions 'connect'."""
    user = user_factory()
    processor = VoiceCommandProcessor(user_id=user.id)

    res = processor.get_next_meeting()
    assert res["success"] is False
    assert "connect" in (res["error"] or "").lower()

    res = processor.create_calendar_event("Lunch tomorrow at noon")
    assert res["success"] is False
    assert "connect" in (res["error"] or "").lower()

    res = processor.get_calendar_status()
    assert res["success"] is False
    assert "connect" in (res["error"] or "").lower()


def test_processor_without_user_id_fails_closed():
    processor = VoiceCommandProcessor()
    assert processor.get_next_meeting()["success"] is False
    assert processor.create_calendar_event("x")["success"] is False


# --- command processor uses user-scoped helpers ---------------------------


def test_next_meeting_passes_calling_users_id(app, user_factory):
    user = user_factory()
    events = [
        {
            "id": "e1",
            "summary": "Design review",
            "date": "August 23, 2026",
            "start_time": "09:00 AM",
            "end_time": "10:00 AM",
            "is_all_day": False,
            "htmlLink": "",
            "location": "Room 2",
        }
    ]
    with patch(
        "app.services.google_calendar.list_upcoming_events_for_user", return_value=events
    ) as mock_list:
        res = VoiceCommandProcessor(user_id=user.id).get_next_meeting()

    mock_list.assert_called_once()
    assert mock_list.call_args.args[0] == user.id
    assert res["success"] is True
    assert "Design review" in res["user_message"]
    assert "Room 2" in res["user_message"]


def test_create_quick_event_passes_calling_users_id_and_text(app, user_factory):
    user = user_factory()
    result = {
        "success": True,
        "event": {"summary": "Lunch", "date": "August 23, 2026", "start_time": "12:00 PM"},
        "message": "Event created: 'Lunch' on August 23, 2026 at 12:00 PM",
    }
    with patch(
        "app.services.google_calendar.create_quick_event_for_user", return_value=result
    ) as mock_create:
        res = VoiceCommandProcessor(user_id=user.id).create_calendar_event(
            "Schedule lunch tomorrow at noon"
        )

    mock_create.assert_called_once_with(user.id, "Schedule lunch tomorrow at noon")
    assert res["success"] is True
    assert "Is there anything else" in res["user_message"]


# --- normalization + isolation --------------------------------------------


def test_list_upcoming_events_for_user_normalizes_events(app, user_factory):
    user = user_factory()
    user.google_credentials = {"token": "t"}
    db.session.commit()

    mock_creds = MagicMock()
    mock_creds.expired = False
    fake_service = _fake_service(items=[_raw_event()])

    with patch("app.services.google_calendar.Credentials") as mock_creds_cls, patch(
        "app.services.google_calendar.build", return_value=fake_service
    ):
        mock_creds_cls.from_authorized_user_info.return_value = mock_creds
        events = google_calendar.list_upcoming_events_for_user(user.id, max_results=5)

    assert events[0]["summary"] == "Standup"
    assert events[0]["location"] == "Zoom"
    assert events[0]["start_time"]  # formatted from raw dateTime

    _, kwargs = fake_service.events().list.call_args
    assert kwargs["calendarId"] == "primary"


def test_users_are_isolated(app, user_factory):
    """A connected user gets a service; another user without creds gets None."""
    connected = user_factory(email="connected@example.com")
    other = user_factory(email="other@example.com")
    connected.google_credentials = {"token": "t"}
    db.session.commit()

    with patch("app.services.google_calendar.Credentials") as mock_creds_cls, patch(
        "app.services.google_calendar.build"
    ) as mock_build:
        mock_creds_cls.from_authorized_user_info.return_value = MagicMock(expired=False)
        assert google_calendar.get_service_for_user(connected.id) is not None
        assert google_calendar.get_service_for_user(other.id) is None

    mock_build.assert_called_once()
