"""Regression tests: malformed or non-positive durations must return 400
instead of raising an unhandled ValueError (HTTP 500) or persisting bad rows."""
from app.extensions import db
from app.models import Meeting


def test_create_meeting_rejects_non_integer_duration(client, user_factory, auth_headers):
    user = user_factory(email="dur-a@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/meetings",
        json={"title": "Bad duration", "start_time": "2026-09-01T10:00:00", "duration": "abc"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_create_meeting_rejects_negative_duration(client, user_factory, auth_headers):
    user = user_factory(email="dur-b@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/meetings",
        json={"title": "Neg duration", "start_time": "2026-09-01T10:00:00", "duration": -5},
        headers=headers,
    )
    assert resp.status_code == 400
    assert Meeting.query.count() == 0


def test_update_meeting_rejects_bad_duration(client, user_factory, auth_headers):
    user = user_factory(email="dur-c@example.com")
    headers = auth_headers(user.id)

    created = client.post(
        "/api/meetings",
        json={"title": "Update target", "start_time": "2026-09-01T10:00:00"},
        headers=headers,
    )
    meeting_id = created.get_json()["meeting"]["id"]

    resp = client.put(
        f"/api/meetings/{meeting_id}", json={"duration": "soon"}, headers=headers
    )
    assert resp.status_code == 400

    with client.application.app_context():
        meeting = db.session.get(Meeting, meeting_id)
        assert meeting.duration_minutes == 30  # default untouched


def test_calendar_sync_rejects_non_integer_duration(client, user_factory, auth_headers):
    user = user_factory(email="dur-d@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/calendar/sync",
        json={"title": "Sync bad", "start": "2026-09-01T10:00:00", "duration_minutes": "abc"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_structured_event_rejects_zero_duration(client, user_factory, auth_headers):
    user = user_factory(email="dur-e@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/calendar/events",
        json={"title": "Zero", "start": "2026-09-01T10:00:00", "duration_minutes": 0},
        headers=headers,
    )
    assert resp.status_code == 400
