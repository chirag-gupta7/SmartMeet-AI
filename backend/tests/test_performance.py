import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services import elevenlabs_service
from backend.app.services.elevenlabs_service import synthesize_speech, _memoized_synthesize

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["ELEVENLABS_API_KEY"] = "test-key"
    app.config["ELEVENLABS_VOICE_ID"] = "test-voice"

    # Reset singleton state and cache before each test
    elevenlabs_service._client = None
    elevenlabs_service._last_api_key = None
    _memoized_synthesize.cache_clear()

    return app

def test_elevenlabs_client_instantiation_count(app):
    """Verify that client is instantiated only once (singleton)."""
    with app.app_context():
        with patch("backend.app.services.elevenlabs_service.ElevenLabs") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance
            mock_client_instance.text_to_speech.convert.return_value = [b"audio"]

            # Call twice
            synthesize_speech("Hello")
            synthesize_speech("World") # Different text to ensure it's not the cache hitting

            # Check how many times the client was instantiated
            # Should be 1 now
            assert mock_client_class.call_count == 1

def test_elevenlabs_api_call_count(app):
    """Verify that results are cached (memoization)."""
    with app.app_context():
        with patch("backend.app.services.elevenlabs_service.ElevenLabs") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance
            mock_client_instance.text_to_speech.convert.return_value = [b"audio"]

            # Call twice with same text
            synthesize_speech("Hello")
            synthesize_speech("Hello")

            # Check how many times convert was called
            # Should be 1 now
            assert mock_client_instance.text_to_speech.convert.call_count == 1
