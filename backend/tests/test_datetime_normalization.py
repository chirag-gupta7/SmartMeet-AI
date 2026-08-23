"""Regression tests: datetimes sent with offsets (Z / +05:30) are normalized
to naive UTC before storage, and the local-events window filter uses naive
UTC so aware/naive values never mix inside a query."""
from datetime import datetime

from app.extensions import db
from app.models import Meeting


def _headers(client, user_factory, auth_headers, email):
    user = user_factory(email=email)
    return auth_headers(user.id)


def test_create_meeting_with_offset_start_is_stored_as_naive_utc(
    client, user_factory, auth_headers
):
    headers = _headers(client, user_factory, auth_headers, "tz-meet@example.com")

    resp = client.post(
        "/api/meetings",
        json={"title": "Offset meeting", "start_time": "2026-09-01T10:00:00+05:30"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()["meeting"]

    # 10:00 +05:30 == 04:30 UTC; stored value must be naive (no offset suffix).
    assert data["start_time"] == "2026-09-01T04:30:00"

    with client.application.app_context():
        stored = db.session.get(Meeting, data["id"])
        assert stored.start_time.tzinfo is None
        assert stored.start_time == datetime(2026, 9, 1, 4, 30)


def test_update_meeting_with_z_suffix_is_normalized(client, user_factory, auth_headers):
    headers = _headers(client, user_factory, auth_headers, "tz-update@example.com")

    created = client.post(
        "/api/meetings",
        json={"title": "Z update", "start_time": "2026-09-02T09:00:00"},
        headers=headers,
    )
    meeting_id = created.get_json()["meeting"]["id"]

    resp = client.put(
        f"/api/meetings/{meeting_id}",
        json={"start_time": "2026-09-02T12:00:00Z"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["meeting"]["start_time"] == "2026-09-02T12:00:00"


def test_structured_event_with_offset_start_is_stored_naive_utc(
    client, user_factory, auth_headers
):
    headers = _headers(client, user_factory, auth_headers, "tz-event@example.com")

    resp = client.post(
        "/api/calendar/events",
        json={
            "title": "Structured offset",
            "start": "2026-09-03T08:00:00-04:00",
            "duration_minutes": 30,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    event = resp.get_json()["event"]

    # 08:00 -04:00 == 12:00 UTC.
    assert event["start"] == "2026-09-03T12:00:00"


def test_local_events_listing_includes_recent_meeting(client, user_factory, auth_headers):
    """The window filter previously mixed an aware 'now' with naive stored
    values; it must query in the same convention as storage."""
    headers = _headers(client, user_factory, auth_headers, "tz-list@example.com")

    created = client.post(
        "/api/meetings",
        json={
            "title": "Recent",
            "start_time": "2026-09-05T10:00:00",
            "duration": 20,
        },
        headers=headers,
    )
    meeting_id = created.get_json()["meeting"]["id"]

    listed = client.get("/api/calendar/events", headers=headers)
    assert listed.status_code == 200
    assert listed.get_json()["source"] == "local"
    ids = [e["id"] for e in listed.get_json()["events"]]
    assert meeting_id in ids
