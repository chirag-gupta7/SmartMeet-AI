import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services import llm_service, elevenlabs_service

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["HUGGINGFACE_API_KEY"] = "fake_hf_key"
    app.config["ELEVENLABS_API_KEY"] = "fake_el_key"
    return app

@pytest.fixture(autouse=True)
def clear_caches():
    # Clear caches before each test
    llm_service._get_llm_response_memoized.cache_clear()
    elevenlabs_service._synthesize_speech_memoized.cache_clear()
    # Reset singletons
    llm_service._client = None
    llm_service._last_api_key = None
    elevenlabs_service._client = None
    elevenlabs_service._last_api_key = None

def test_llm_client_singleton(app):
    with app.app_context():
        with patch("backend.app.services.llm_service.InferenceClient") as mock_client_class:
            mock_instance = mock_client_class.return_value
            mock_instance.chat_completion.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"action": "general_response", "reply": "Hi"}'))]
            )

            # _get_client() should return same instance
            c1 = llm_service._get_client()
            c2 = llm_service._get_client()

            assert c1 is c2
            assert mock_client_class.call_count == 1

def test_llm_memoization(app):
    with app.app_context():
        # Patch InferenceClient where it's used in the memoized helper
        with patch("backend.app.services.llm_service.InferenceClient") as mock_client_class:
            mock_instance = mock_client_class.return_value
            mock_instance.chat_completion.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"action": "general_response", "reply": "Hi"}'))]
            )

            # Same input twice
            llm_service.generate_action_reply("hello")
            llm_service.generate_action_reply("hello")

            # Should be memoized, so chat_completion called only once
            assert mock_instance.chat_completion.call_count == 1

def test_elevenlabs_client_singleton(app):
    with app.app_context():
        with patch("backend.app.services.elevenlabs_service.ElevenLabs") as mock_client_class:
            c1 = elevenlabs_service._get_client()
            c2 = elevenlabs_service._get_client()

            assert c1 is c2
            assert mock_client_class.call_count == 1

def test_elevenlabs_memoization(app):
    with app.app_context():
        with patch("backend.app.services.elevenlabs_service.ElevenLabs") as mock_client_class:
            mock_instance = mock_client_class.return_value
            mock_instance.text_to_speech.convert.return_value = [b"audio_data"]

            elevenlabs_service.synthesize_speech("hello")
            elevenlabs_service.synthesize_speech("hello")

            # Should be memoized
            assert mock_instance.text_to_speech.convert.call_count == 1
