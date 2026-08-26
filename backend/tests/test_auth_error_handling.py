"""Regression tests for authentication error handling and input validation."""
import logging
from unittest.mock import patch


def test_google_login_failure_returns_generic_message_and_logs_detail(
    client, caplog
):
    error_msg = "secret redirect_uri https://internal.example.com leaked"
    with patch(
        "app.routes.auth.InstalledAppFlow.from_client_secrets_file",
        side_effect=Exception(error_msg),
    ):
        with caplog.at_level(logging.WARNING, logger="app.routes.auth"):
            resp = client.post("/api/auth/google", json={"code": "some-code"})

    assert resp.status_code == 500
    body = resp.get_json()
    assert body["message"] == "Google authentication failed. Please try again."
    # Raw exception detail must stay in server logs only.
    assert "leaked" not in body["message"]
    assert any(
        "leaked" in r.getMessage() for r in caplog.records
    )


def test_register_non_string_fields_returns_400(client):
    """Non-string inputs in register must be rejected with 400."""
    payload = {
        "name": 12345,
        "email": "valid@example.com",
        "password": "password",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert "required" in resp.get_json()["message"]


def test_register_oversized_input_fields_returns_400(client):
    """Oversized name or email in register must be rejected with 400."""
    long_name = "A" * 121
    payload = {
        "name": long_name,
        "email": "valid@example.com",
        "password": "password",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert "exceed" in resp.get_json()["message"]


def test_login_non_string_fields_returns_401(client):
    """Non-string inputs in login must be rejected with 401."""
    payload = {"email": 12345, "password": ["secret"]}
    resp = client.post("/api/auth/login", json=payload)
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.get_json()["message"]


def test_update_user_non_string_or_oversized_name_returns_400(
    client, user_factory, auth_headers
):
    """Updating user with non-string or oversized name returns 400."""
    user = user_factory()
    headers = auth_headers(user.id)

    resp1 = client.patch(
        "/api/auth/me",
        json={"name": 12345},
        headers=headers,
    )
    assert resp1.status_code == 400

    resp2 = client.patch(
        "/api/auth/me",
        json={"name": "A" * 121},
        headers=headers,
    )
    assert resp2.status_code == 400
    assert "120 characters" in resp2.get_json()["message"]
