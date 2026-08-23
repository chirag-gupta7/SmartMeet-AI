"""Regression: a concurrent duplicate registration used to surface an
unhandled IntegrityError (HTTP 500); it must map to the same 409 as the
pre-check path."""
from unittest.mock import patch

from app.extensions import db
from app.models import User
from app.routes import auth


def test_register_maps_integrity_error_to_409(client, user_factory):
    # An existing row with the same email; the pre-check is bypassed below
    # so the UNIQUE constraint itself fires during commit.
    user_factory(email="race@example.com")

    with patch.object(auth.User, "query") as mock_query:
        mock_query.filter_by.return_value.first.return_value = None

        resp = client.post(
            "/api/auth/register",
            json={
                "name": "Racer",
                "email": "race@example.com",
                "password": "password123",
            },
        )

    assert resp.status_code == 409
    assert resp.get_json()["message"] == "Email already registered"

    # The rollback must have left the session usable for normal work.
    with client.application.app_context():
        assert db.session.get(User, "nonexistent-id") is None


def test_register_still_rejects_duplicate_email_via_precheck(client):
    payload = {
        "name": "First",
        "email": "dup@example.com",
        "password": "password123",
    }
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code in (200, 201)

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409
