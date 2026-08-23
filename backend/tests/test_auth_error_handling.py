"""Regression: the Google OAuth error path used to return raw str(exc) to
the client and log via print(); it must log server-side and reply generically."""
import logging
from unittest.mock import patch

from app.routes.auth import auth_bp


def test_google_login_failure_returns_generic_message_and_logs_detail(
    client, caplog
):
    with patch(
        "app.routes.auth.InstalledAppFlow.from_client_secrets_file",
        side_effect=Exception("secret redirect_uri https://internal.example.com leaked"),
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
