import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to path so we can import app
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services import elevenlabs_service
from app.services.elevenlabs_service import synthesize_speech, _synthesize_speech_memoized

@pytest.fixture(autouse=True)
def clear_caches():
    _synthesize_speech_memoized.cache_clear()
    elevenlabs_service._client_cache.clear()

def test_synthesize_speech_memoization():
    mock_app = MagicMock()
    mock_app.config = {
        "ELEVENLABS_API_KEY": "test_key",
        "ELEVENLABS_VOICE_ID": "test_voice"
    }

    with patch("app.services.elevenlabs_service.current_app", mock_app):
        with patch("app.services.elevenlabs_service.ElevenLabs") as MockElevenLabs:
            mock_client = MockElevenLabs.return_value
            # Mock the response to be an iterable of bytes
            mock_client.text_to_speech.convert.return_value = [b"audio_data"]

            # First call
            res1 = synthesize_speech("Hello")
            assert res1 is not None

            # Second call with same text
            res2 = synthesize_speech("Hello")
            assert res2 == res1

            # Verify convert was called only once
            assert mock_client.text_to_speech.convert.call_count == 1

            # Call with different text
            res3 = synthesize_speech("World")
            assert res3 is not None
            assert mock_client.text_to_speech.convert.call_count == 2

def test_client_caching():
    mock_app = MagicMock()
    mock_app.config = {
        "ELEVENLABS_API_KEY": "test_key",
        "ELEVENLABS_VOICE_ID": "test_voice"
    }

    with patch("app.services.elevenlabs_service.current_app", mock_app):
        with patch("app.services.elevenlabs_service.ElevenLabs") as MockElevenLabs:
            mock_client = MockElevenLabs.return_value
            mock_client.text_to_speech.convert.return_value = [b"audio_data"]

            synthesize_speech("Hello")
            synthesize_speech("World")

            # ElevenLabs client should be initialized only once for the same API key
            assert MockElevenLabs.call_count == 1

def test_do_not_cache_failures():
    mock_app = MagicMock()
    mock_app.config = {
        "ELEVENLABS_API_KEY": "test_key",
        "ELEVENLABS_VOICE_ID": "test_voice"
    }

    with patch("app.services.elevenlabs_service.current_app", mock_app):
        with patch("app.services.elevenlabs_service.ElevenLabs") as MockElevenLabs:
            mock_client = MockElevenLabs.return_value

            # First call fails
            mock_client.text_to_speech.convert.side_effect = Exception("API Error")
            res1 = synthesize_speech("Retry")
            assert res1 is None
            assert mock_client.text_to_speech.convert.call_count == 1

            # Second call succeeds
            mock_client.text_to_speech.convert.side_effect = None
            mock_client.text_to_speech.convert.return_value = [b"success_audio"]
            res2 = synthesize_speech("Retry")
            assert res2 is not None
            # Should have called convert again because the failure wasn't cached
            assert mock_client.text_to_speech.convert.call_count == 2
