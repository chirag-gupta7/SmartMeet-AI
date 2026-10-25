from unittest.mock import MagicMock, patch

from app.services import google_calendar


def test_build_service_validates_token():
    # Non-string token
    assert google_calendar._build_service(12345) is None
    # Empty / whitespace token
    assert google_calendar._build_service("   ") is None
    # Oversized token
    assert google_calendar._build_service("a" * 4097) is None


def test_create_event_validates_payload():
    # Non-dict event payload
    assert google_calendar.create_event("valid_token", "not_a_dict") is None


def test_list_upcoming_events_clamps_parameters():
    mock_service = MagicMock()
    mock_service.events().list.return_value.execute.return_value = {"items": []}

    with patch("app.services.google_calendar._build_service", return_value=mock_service):
        # Test negative max_results and days_ahead
        google_calendar.list_upcoming_events("token", max_results=-10, days_ahead=-5)
        _, kwargs = mock_service.events().list.call_args
        assert kwargs["maxResults"] == 1

        # Test oversized max_results (> 250) and days_ahead (> 365)
        google_calendar.list_upcoming_events("token", max_results=1000, days_ahead=1000)
        _, kwargs = mock_service.events().list.call_args
        assert kwargs["maxResults"] == 250

        # Test invalid string types for numerical arguments
        google_calendar.list_upcoming_events("token", max_results="invalid", days_ahead="invalid")
        _, kwargs = mock_service.events().list.call_args
        assert kwargs["maxResults"] == 10


def test_list_upcoming_events_for_user_clamps_parameters(app, user_factory):
    user = user_factory()
    mock_service = MagicMock()
    mock_service.events().list.return_value.execute.return_value = {"items": []}

    with patch(
        "app.services.google_calendar.get_service_for_user", return_value=mock_service
    ):
        # Oversized max_results & days_ahead
        google_calendar.list_upcoming_events_for_user(
            user.id, max_results=500, days_ahead=500
        )
        _, kwargs = mock_service.events().list.call_args
        assert kwargs["maxResults"] == 250

        # Negative max_results & days_ahead
        google_calendar.list_upcoming_events_for_user(
            user.id, max_results=-5, days_ahead=-10
        )
        _, kwargs = mock_service.events().list.call_args
        assert kwargs["maxResults"] == 1

        # Invalid strings
        google_calendar.list_upcoming_events_for_user(
            user.id, max_results="abc", days_ahead="xyz"
        )
        _, kwargs = mock_service.events().list.call_args
        assert kwargs["maxResults"] == 10
