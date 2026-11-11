from unittest.mock import patch
from app.services.llm_service import generate_action_reply
from app.services.elevenlabs_service import synthesize_speech


def test_generate_action_reply_non_string_and_empty(app):
    with app.app_context():
        invalid_inputs = [None, 123, [], {}, "", "   "]
        for inp in invalid_inputs:
            action, reply = generate_action_reply(inp)
            assert action == "general_response"
            assert reply == "I didn't hear anything."


def test_generate_action_reply_oversized_string(app):
    with app.app_context():
        app.config["HUGGINGFACE_API_KEY"] = "fake_hf_key"
        oversized = "A" * 6000
        with patch("app.services.llm_service._memoized_generate_action_reply") as mock_memo:
            action, reply = generate_action_reply(oversized)
            assert action == "general_response"
            assert reply == "Input text is too long."
            assert mock_memo.call_count == 0


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
            res = synthesize_speech(oversized)
            assert res is None
            assert mock_memo.call_count == 0
