"""Regression tests for meeting ownership and validation in meetings.py."""
from app.extensions import db
from app.models import Meeting


def _create_meeting_via_api(client, headers, title="Team sync"):
    return client.post(
        "/api/meetings",
        json={
            "title": title,
            "start_time": "2026-09-01T10:00:00",
            "duration": 45,
        },
        headers=headers,
    )


def test_owner_can_list_create_update_delete_own_meetings(
    app, client, user_factory, auth_headers
):
    user = user_factory(email="owner@example.com")
    headers = auth_headers(user.id)

    resp = _create_meeting_via_api(client, headers)
    assert resp.status_code == 201
    meeting_id = resp.get_json()["meeting"]["id"]

    listed = client.get("/api/meetings", headers=headers)
    assert listed.status_code == 200
    assert [m["id"] for m in listed.get_json()["meetings"]] == [meeting_id]

    updated = client.put(
        f"/api/meetings/{meeting_id}",
        json={"title": "Renamed"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.get_json()["meeting"]["title"] == "Renamed"

    deleted = client.delete(f"/api/meetings/{meeting_id}", headers=headers)
    assert deleted.status_code == 200
    with app.app_context():
        assert db.session.get(Meeting, meeting_id) is None


def test_other_user_cannot_see_update_or_delete_foreign_meeting(
    app, client, user_factory, auth_headers
):
    owner = user_factory(email="owner2@example.com")
    intruder = user_factory(email="intruder@example.com")
    owner_headers = auth_headers(owner.id)
    intruder_headers = auth_headers(intruder.id)

    created = _create_meeting_via_api(client, owner_headers)
    assert created.status_code == 201
    meeting_id = created.get_json()["meeting"]["id"]

    # Intruder's list must not include the owner's meeting.
    listed = client.get("/api/meetings", headers=intruder_headers)
    assert listed.status_code == 200
    assert listed.get_json()["meetings"] == []

    # Direct access to the foreign id must 404, not leak data.
    fetched = client.put(
        f"/api/meetings/{meeting_id}",
        json={"title": "Hijacked"},
        headers=intruder_headers,
    )
    assert fetched.status_code == 404

    deleted = client.delete(
        f"/api/meetings/{meeting_id}", headers=intruder_headers
    )
    assert deleted.status_code == 404

    # The owner's meeting is untouched.
    with app.app_context():
        meeting = db.session.get(Meeting, meeting_id)
        assert meeting is not None
        assert meeting.title == "Team sync"
        assert meeting.owner_id == owner.id


def test_create_meeting_title_validation(client, user_factory, auth_headers):
    user = user_factory(email="validation_create@example.com")
    headers = auth_headers(user.id)

    # Non-string title
    resp = client.post(
        "/api/meetings",
        json={"title": 12345, "start_time": "2026-09-01T10:00:00"},
        headers=headers,
    )
    assert resp.status_code == 400

    # Exceeding 255 chars
    resp = client.post(
        "/api/meetings",
        json={"title": "a" * 256, "start_time": "2026-09-01T10:00:00"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_update_meeting_title_validation(client, user_factory, auth_headers):
    user = user_factory(email="validation_update@example.com")
    headers = auth_headers(user.id)

    created = _create_meeting_via_api(client, headers)
    meeting_id = created.get_json()["meeting"]["id"]

    # Non-string title on update
    resp = client.put(
        f"/api/meetings/{meeting_id}",
        json={"title": 12345},
        headers=headers,
    )
    assert resp.status_code == 400

    # Exceeding 255 chars on update
    resp = client.put(
        f"/api/meetings/{meeting_id}",
        json={"title": "a" * 256},
        headers=headers,
    )
    assert resp.status_code == 400
