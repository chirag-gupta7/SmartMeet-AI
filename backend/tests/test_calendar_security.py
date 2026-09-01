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
