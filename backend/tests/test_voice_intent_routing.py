"""Regression tests: general (non-scheduling, non-weather) transcripts now
reach VoiceCommandProcessor.detect_and_process via /api/voice/process."""
from unittest.mock import patch

from app.models import Note


def _post_transcript(client, headers, transcript):
    return client.post(
        "/api/voice/process",
        json={"transcript": transcript},
        headers=headers,
    )


def _general_llm():
    return patch(
        "app.routes.voice.generate_action_reply",
        return_value=("general_response", "Here is a generic answer."),
    )


def test_joke_transcript_routes_to_joke_command(client, user_factory, auth_headers):
    user = user_factory(email="voice-joke@example.com")
    headers = auth_headers(user.id)

    with _general_llm():
        resp = _post_transcript(client, headers, "tell me a joke")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["command_result"] is not None
    assert "joke" in data["command_result"]["data"]


def test_note_transcript_persists_a_note_row(client, user_factory, auth_headers):
    user = user_factory(email="voice-note@example.com")
    headers = auth_headers(user.id)

    with _general_llm():
        resp = _post_transcript(client, headers, "take a note buy milk after work")

    assert resp.status_code == 200
    note = Note.query.filter_by(user_id=user.id).first()
    assert note is not None
    assert "buy milk" in note.content


def test_calculate_transcript_returns_computed_result(client, user_factory, auth_headers):
    user = user_factory(email="voice-calc@example.com")
    headers = auth_headers(user.id)

    with _general_llm():
        resp = _post_transcript(client, headers, "calculate 12*3")

    data = resp.get_json()
    assert data["command_result"]["success"] is True
    assert data["command_result"]["data"]["result"] == 36


def test_calculate_transcript_exponent_limit_prevents_dos(
    client, user_factory, auth_headers
):
    user = user_factory(email="voice-calc-dos@example.com")
    headers = auth_headers(user.id)

    with _general_llm():
        resp = _post_transcript(client, headers, "calculate 2**1000000")

    data = resp.get_json()
    assert data["command_result"]["success"] is False
    assert "Exponent too large" in data["command_result"]["error"]


def test_unmatched_general_transcript_keeps_llm_reply(client, user_factory, auth_headers):
    user = user_factory(email="voice-hello@example.com")
    headers = auth_headers(user.id)

    with _general_llm():
        resp = _post_transcript(client, headers, "hello there nice robot")

    data = resp.get_json()
    assert data["success"] is True
    # Nothing matched: no command result, the LLM reply stands.
    assert data["command_result"] is None
    assert data["message"] == "Here is a generic answer."


def test_weather_keyword_still_routes_to_weather(client, user_factory, auth_headers):
    user = user_factory(email="voice-weather@example.com")
    headers = auth_headers(user.id)

    with _general_llm():
        resp = _post_transcript(client, headers, "what's the weather like?")

    data = resp.get_json()
    assert data["success"] is True
    assert data["command_result"] is not None
    assert "weather" in data["message"].lower() or "sunny" in data["message"].lower()


def test_schedule_meeting_action_still_takes_priority(client, user_factory, auth_headers):
    """A scheduling intent must not be hijacked by the general detector."""
    user = user_factory(email="voice-sched@example.com")
    headers = auth_headers(user.id)

    with patch(
        "app.routes.voice.generate_action_reply", return_value=("schedule_meeting", "Scheduling.")
    ), patch(
        "app.routes.voice.VoiceCommandProcessor"
    ) as mock_processor_cls:
        instance = mock_processor_cls.return_value
        instance.create_calendar_event.return_value = {
            "success": True,
            "user_message": "Scheduled!",
        }

        resp = _post_transcript(client, headers, "schedule lunch tomorrow at noon")

        instance.create_calendar_event.assert_called_once_with(
            "schedule lunch tomorrow at noon"
        )
        assert resp.get_json()["message"] == "Scheduled!"


def test_invalid_transcript_type_returns_400(
    client, user_factory, auth_headers
):
    user = user_factory(email="voice-invalid-type@example.com")
    headers = auth_headers(user.id)

    resp = client.post(
        "/api/voice/process",
        json={"transcript": 12345},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "Transcript is required"


def test_oversized_transcript_returns_400(
    client, user_factory, auth_headers
):
    user = user_factory(email="voice-oversized@example.com")
    headers = auth_headers(user.id)

    oversized_text = "a" * 5001
    resp = _post_transcript(client, headers, oversized_text)
    assert resp.status_code == 400
    assert "exceeds maximum allowed length" in resp.get_json()["message"]
