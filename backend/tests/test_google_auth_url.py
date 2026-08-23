"""Regression: get_auth_url's default redirect must match the frontend's
/auth/callback route (the old default was :3000/oauth2callback, a route
that does not exist in the React app)."""
from unittest.mock import MagicMock, patch

from app.services import google_calendar


def test_get_auth_url_defaults_to_frontend_auth_callback(app, monkeypatch):
    # A stale GOOGLE_REDIRECT_URI in a local .env must not leak into this
    # test - we are asserting the built-in default.
    monkeypatch.delenv("GOOGLE_REDIRECT_URI", raising=False)
    flow = MagicMock()
    flow.authorization_url.return_value = ("https://accounts.google.com/o/oauth2/auth?x=1", None)

    with patch(
        "app.services.google_calendar.InstalledAppFlow"
    ) as mock_flow_cls, patch("os.path.join", return_value="credentials.json"), patch(
        "os.path.exists", return_value=True
    ):
        mock_flow_cls.from_client_secrets_file.return_value = flow

        # credentials file existence is checked by from_client_secrets_file;
        # the mock bypasses it, so no real file is needed.
        url = google_calendar.get_auth_url()

        assert mock_flow_cls.from_client_secrets_file.called
        assert flow.redirect_uri == "http://localhost:3000/auth/callback"
        assert url == "https://accounts.google.com/o/oauth2/auth?x=1"


def test_get_auth_url_respects_explicit_redirect_override(app, monkeypatch):
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://app.example.com/auth/callback")
    flow = MagicMock()
    flow.authorization_url.return_value = ("https://accounts.google.com/o/oauth2/auth?y=2", None)

    with patch(
        "app.services.google_calendar.InstalledAppFlow"
    ) as mock_flow_cls:
        mock_flow_cls.from_client_secrets_file.return_value = flow
        google_calendar.get_auth_url()

    assert flow.redirect_uri == "https://app.example.com/auth/callback"


def test_get_auth_url_uses_configured_frontend_url(app, monkeypatch):
    monkeypatch.delenv("GOOGLE_REDIRECT_URI", raising=False)
    app.config["FRONTEND_URL"] = "https://meet.example.com"
    flow = MagicMock()
    flow.authorization_url.return_value = ("https://accounts.google.com/o/oauth2/auth?z=3", None)

    with patch(
        "app.services.google_calendar.InstalledAppFlow"
    ) as mock_flow_cls:
        mock_flow_cls.from_client_secrets_file.return_value = flow
        google_calendar.get_auth_url()

    assert flow.redirect_uri == "https://meet.example.com/auth/callback"
