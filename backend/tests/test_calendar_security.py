import pytest
from app.models import User, db


@pytest.fixture
def auth_headers(app, client):
    with app.app_context():
        user = User(name="Calendar Test User", email="caluser@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    res = client.post(
        "/api/auth/login",
        json={"email": "caluser@example.com", "password": "password123"},
    )
    token = res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_sync_calendar_invalid_title(client, auth_headers):
    # Non-string title
    res = client.post(
        "/api/calendar/sync",
        headers=auth_headers,
        json={"title": 12345, "start": "2026-05-01T10:00:00Z"},
    )
    assert res.status_code == 400
    assert "title and start are required" in res.get_json()["message"]

    # Oversized title
    res = client.post(
        "/api/calendar/sync",
        headers=auth_headers,
        json={"title": "A" * 256, "start": "2026-05-01T10:00:00Z"},
    )
    assert res.status_code == 400
    assert "255 characters or fewer" in res.get_json()["message"]


def test_google_calendar_token_and_parameter_clamping():
    from app.services.google_calendar import (
        _build_service,
        create_event,
        list_upcoming_events,
    )

    # _build_service rejects non-string or oversized tokens
    assert _build_service(12345) is None
    assert _build_service("x" * 4097) is None

    # create_event rejects non-dict event payloads
    assert create_event("valid_token", "not a dict") is None

    # list_upcoming_events handles extreme days_ahead without OverflowError
    events = list_upcoming_events(
        access_token="invalid_token",
        max_results=10000,
        days_ahead=10**20,
    )
    assert events == []


def test_oversized_google_access_token_header_ignored(client, auth_headers):
    headers = dict(auth_headers)
    headers["X-Google-Access-Token"] = "A" * 5000

    res = client.get("/api/calendar/events", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["source"] == "local"


def test_create_structured_event_invalid_timezone_and_notifications(
    client, auth_headers
):
    # Non-string time_zone
    res = client.post(
        "/api/calendar/events",
        headers=auth_headers,
        json={
            "title": "Meeting",
            "start": "2026-05-01T10:00:00Z",
            "time_zone": 12345,
        },
    )
    assert res.status_code == 400
    assert "time_zone must be a string" in res.get_json()["message"]

    # Oversized time_zone
    res = client.post(
        "/api/calendar/events",
        headers=auth_headers,
        json={
            "title": "Meeting",
            "start": "2026-05-01T10:00:00Z",
            "time_zone": "Z" * 65,
        },
    )
    assert res.status_code == 400
    assert "64 characters or fewer" in res.get_json()["message"]

    # Non-list notifications
    res = client.post(
        "/api/calendar/events",
        headers=auth_headers,
        json={
            "title": "Meeting",
            "start": "2026-05-01T10:00:00Z",
            "notifications": "10",
        },
    )
    assert res.status_code == 400
    assert "notifications must be a list" in res.get_json()["message"]


def test_sync_calendar_invalid_description(client, auth_headers):
    # Non-string description
    res = client.post(
        "/api/calendar/sync",
        headers=auth_headers,
        json={
            "title": "Meeting",
            "start": "2026-05-01T10:00:00Z",
            "description": ["invalid", "type"],
        },
    )
    assert res.status_code == 400
    assert "description must be a string" in res.get_json()["message"]

    # Oversized description
    res = client.post(
        "/api/calendar/sync",
        headers=auth_headers,
        json={
            "title": "Meeting",
            "start": "2026-05-01T10:00:00Z",
            "description": "B" * 10001,
        },
    )
    assert res.status_code == 400
    assert "10000 characters" in res.get_json()["message"]


def test_create_structured_event_invalid_inputs(client, auth_headers):
    # Non-string location
    res = client.post(
        "/api/calendar/events",
        headers=auth_headers,
        json={
            "title": "Meeting",
            "start": "2026-05-01T10:00:00Z",
            "location": {"room": 101},
        },
    )
    assert res.status_code == 400
    assert "location must be a string" in res.get_json()["message"]

    # Oversized location
    res = client.post(
        "/api/calendar/events",
        headers=auth_headers,
        json={
            "title": "Meeting",
            "start": "2026-05-01T10:00:00Z",
            "location": "C" * 256,
        },
    )
    assert res.status_code == 400
    assert "255 characters or fewer" in res.get_json()["message"]
