
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["ELEVENLABS_API_KEY"] = "fake_key"
    app.config["ELEVENLABS_VOICE_ID"] = "fake_voice"
    return app

def test_synthesize_speech_caching(app):
    import backend.app.services.elevenlabs_service as service

    # Reset global state
    service._client = None
    service._last_api_key = None
    service._synthesize_cached.cache_clear()

    with app.app_context():
        with patch('backend.app.services.elevenlabs_service.ElevenLabs') as mock_eleven:
            mock_client = MagicMock()
            mock_eleven.return_value = mock_client
            mock_client.text_to_speech.convert.return_value = [b"audio", b"data"]

            text = "Hello world"

            # First call
            res1 = service.synthesize_speech(text)
            # Second call (should be cached)
            res2 = service.synthesize_speech(text)

            assert res1 == res2
            assert res1 is not None

            # Client should be instantiated only once
            assert mock_eleven.call_count == 1
            # text_to_speech.convert should be called only once
            assert mock_client.text_to_speech.convert.call_count == 1

def test_synthesize_speech_cache_invalidation_on_config_change(app):
    import backend.app.services.elevenlabs_service as service

    service._client = None
    service._last_api_key = None
    service._synthesize_cached.cache_clear()

    with app.app_context():
        with patch('backend.app.services.elevenlabs_service.ElevenLabs') as mock_eleven:
            mock_client = MagicMock()
            mock_eleven.return_value = mock_client
            mock_client.text_to_speech.convert.return_value = [b"audio"]

            text = "Hello world"

            # First call with original config
            service.synthesize_speech(text)
            assert mock_eleven.call_count == 1
            assert mock_client.text_to_speech.convert.call_count == 1

            # Change API key
            app.config["ELEVENLABS_API_KEY"] = "new_key"
            service.synthesize_speech(text)

            # Client should be re-instantiated
            assert mock_eleven.call_count == 2
            # convert should be called again because api_key changed in lru_cache key
            assert mock_client.text_to_speech.convert.call_count == 2
