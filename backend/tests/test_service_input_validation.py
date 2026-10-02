from unittest.mock import patch
from app.services.llm_service import generate_action_reply
from app.services.elevenlabs_service import synthesize_speech


def test_generate_action_reply_non_string_and_empty(app):
    with app.app_context():
        invalid_inputs = [None, 123, [], {}, "", "   "]
        for inp in invalid_inputs:
            action, reply = generate_action_reply(inp)
            assert action == "general_response"
            assert reply == "Please provide valid text."


def test_generate_action_reply_oversized_string(app):
    with app.app_context():
        app.config["HUGGINGFACE_API_KEY"] = "fake_hf_key"
        oversized = "A" * 6000
        with patch("app.services.llm_service._memoized_generate_action_reply") as mock_memo:
            mock_memo.return_value = '{"action": "weather", "reply": "Sunny"}'
            action, reply = generate_action_reply(oversized)
            assert action == "weather"
            assert reply == "Sunny"
            # Verify truncated text (5000 chars) was passed to the memoized generator
            passed_text, _ = mock_memo.call_args[0]
            assert len(passed_text) == 5000


def test_synthesize_speech_non_string_and_empty(app):
    with app.app_context():
        invalid_inputs = [None, 123, [], {}, "", "   "]
        for inp in invalid_inputs:
            res = synthesize_speech(inp)
            assert res is None


def test_synthesize_speech_oversized_string(app):
    with app.app_context():
        app.config["ELEVENLABS_API_KEY"] = "fake_elevenlabs_key"
        oversized = "B" * 6000
        with patch("app.services.elevenlabs_service._synthesize_speech_memoized") as mock_memo:
            mock_memo.return_value = "base64audio"
            res = synthesize_speech(oversized)
            assert res == "base64audio"
            # Verify truncated text (5000 chars) was passed
            _, _, passed_text = mock_memo.call_args[0]
            assert len(passed_text) == 5000
