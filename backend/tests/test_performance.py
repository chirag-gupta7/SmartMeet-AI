import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services.llm_service import (
    generate_action_reply,
    _get_client as get_llm_client,
    _get_cached_client as get_cached_llm_client,
    _generate_action_reply_memoized
)
from backend.app.services.elevenlabs_service import (
    synthesize_speech,
    _get_client as get_tts_client,
    _get_cached_client as get_cached_tts_client,
    _synthesize_speech_memoized
)

@pytest.fixture(autouse=True)
def clear_caches():
    get_cached_llm_client.cache_clear()
    _generate_action_reply_memoized.cache_clear()
    get_cached_tts_client.cache_clear()
    _synthesize_speech_memoized.cache_clear()

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["HUGGINGFACE_API_KEY"] = "fake_hf_key"
    app.config["ELEVENLABS_API_KEY"] = "fake_el_key"
    app.config["ELEVENLABS_VOICE_ID"] = "fake_voice_id"
    return app

def test_llm_client_instantiation(app):
    with app.app_context():
        with patch("backend.app.services.llm_service.InferenceClient") as mock_client:
            # Call multiple times
            get_llm_client()
            get_llm_client()

            # After optimization, this should be 1
            assert mock_client.call_count == 1

def test_llm_memoization(app):
    with app.app_context():
        with patch("backend.app.services.llm_service.InferenceClient") as mock_client_class:
            mock_inst = MagicMock()
            mock_client_class.return_value = mock_inst

            mock_response = MagicMock()
            mock_response.choices[0].message.content = '{"action": "weather", "reply": "Sunny"}'
            mock_inst.chat_completion.return_value = mock_response

            # Call multiple times with same text
            generate_action_reply("What is the weather?")
            generate_action_reply("What is the weather?")

            # After optimization, this should be 1
            assert mock_inst.chat_completion.call_count == 1

def test_tts_client_instantiation(app):
    with app.app_context():
        with patch("backend.app.services.elevenlabs_service.ElevenLabs") as mock_client:
            # Call multiple times
            get_tts_client()
            get_tts_client()

            # After optimization, this should be 1
            assert mock_client.call_count == 1

def test_tts_memoization(app):
    with app.app_context():
        with patch("backend.app.services.elevenlabs_service.ElevenLabs") as mock_client_class:
            mock_inst = MagicMock()
            mock_client_class.return_value = mock_inst

            mock_inst.text_to_speech.convert.return_value = [b"audio", b"data"]

            # Call multiple times with same text
            synthesize_speech("Hello")
            synthesize_speech("Hello")

            # After optimization, this should be 1
            assert mock_inst.text_to_speech.convert.call_count == 1
