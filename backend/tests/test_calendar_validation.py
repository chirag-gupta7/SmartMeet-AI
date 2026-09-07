"""Tests for string type validation and length limits on calendar endpoints."""

from app.models import Meeting


def test_sync_calendar_rejects_non_string_title(
    client, user_factory, auth_headers
):
    user = user_factory(email="calval1@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/calendar/sync",
        json={"title": 12345, "start": "2026-09-01T10:00:00"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_sync_calendar_rejects_oversized_title(
    client, user_factory, auth_headers
):
    user = user_factory(email="calval2@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/calendar/sync",
        json={"title": "A" * 256, "start": "2026-09-01T10:00:00"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_sync_calendar_rejects_invalid_description(
    client, user_factory, auth_headers
):
    user = user_factory(email="calval3@example.com")
    headers = auth_headers(user.id)

    resp_non_str = client.post(
        "/api/calendar/sync",
        json={
            "title": "Valid",
            "start": "2026-09-01T10:00:00",
            "description": 123,
        },
        headers=headers,
    )
    assert resp_non_str.status_code == 400

    resp_oversized = client.post(
        "/api/calendar/sync",
        json={
            "title": "Valid",
            "start": "2026-09-01T10:00:00",
            "description": "B" * 10001,
        },
        headers=headers,
    )
    assert resp_oversized.status_code == 400


def test_create_structured_event_rejects_non_string_title(
    client, user_factory, auth_headers
):
    user = user_factory(email="calval4@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/calendar/events",
        json={"title": 999, "start": "2026-09-01T10:00:00"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_create_structured_event_rejects_oversized_title(
    client, user_factory, auth_headers
):
    user = user_factory(email="calval5@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/calendar/events",
        json={"title": "X" * 300, "start": "2026-09-01T10:00:00"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_create_structured_event_rejects_invalid_location_and_raw_text(
    client, user_factory, auth_headers
):
    user = user_factory(email="calval6@example.com")
    headers = auth_headers(user.id)

    resp_loc_num = client.post(
        "/api/calendar/events",
        json={
            "title": "Valid",
            "start": "2026-09-01T10:00:00",
            "location": 12345,
        },
        headers=headers,
    )
    assert resp_loc_num.status_code == 400

    resp_loc_long = client.post(
        "/api/calendar/events",
        json={
            "title": "Valid",
            "start": "2026-09-01T10:00:00",
            "location": "L" * 256,
        },
        headers=headers,
    )
    assert resp_loc_long.status_code == 400

    resp_text_num = client.post(
        "/api/calendar/events",
        json={
            "title": "Valid",
            "start": "2026-09-01T10:00:00",
            "raw_text": True,
        },
        headers=headers,
    )
    assert resp_text_num.status_code == 400

    resp_text_long = client.post(
        "/api/calendar/events",
        json={
            "title": "Valid",
            "start": "2026-09-01T10:00:00",
            "raw_text": "T" * 10001,
        },
        headers=headers,
    )
    assert resp_text_long.status_code == 400


def test_calendar_endpoints_accept_valid_inputs(
    client, user_factory, auth_headers
):
    user = user_factory(email="calval7@example.com")
    headers = auth_headers(user.id)

    resp_sync = client.post(
        "/api/calendar/sync",
        json={
            "title": "Sync Test",
            "description": "Short description",
            "start": "2026-09-01T10:00:00",
        },
        headers=headers,
    )
    assert resp_sync.status_code == 200
    assert resp_sync.get_json()["success"] is True

    resp_struct = client.post(
        "/api/calendar/events",
        json={
            "title": "Structured Test",
            "description": "A description",
            "start": "2026-09-01T10:00:00",
            "location": "Conference Room A",
            "raw_text": "Schedule structured test tomorrow at 10am",
        },
        headers=headers,
    )
    assert resp_struct.status_code == 201
    assert resp_struct.get_json()["success"] is True

    assert Meeting.query.filter_by(owner_id=user.id).count() == 2
