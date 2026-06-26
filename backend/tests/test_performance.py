import time
import pytest
from unittest.mock import MagicMock, patch
import sys

# Define a mock current_app that doesn't trigger the application context error
class MockConfig(dict):
    def get(self, key, default=None):
        return super().get(key, default)

@pytest.fixture(autouse=True)
def setup_mocks():
    # Force mock flask.current_app BEFORE any imports that might use it
    mock_current_app = MagicMock()
    mock_current_app.config = MockConfig({
        "HUGGINGFACE_API_KEY": "test_hf_key",
        "ELEVENLABS_API_KEY": "test_el_key",
        "ELEVENLABS_VOICE_ID": "test_voice_id"
    })

    with patch('flask.current_app', mock_current_app):
        yield mock_current_app

def test_llm_performance():
    from backend.app.services.llm_service import generate_action_reply, _get_cached_response, _get_cached_client

    # Clear caches
    _get_cached_response.cache_clear()
    _get_cached_client.cache_clear()

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"action": "general_response", "reply": "Hello"}'))]
    mock_client.chat_completion.return_value = mock_response

    with patch('backend.app.services.llm_service.InferenceClient', return_value=mock_client):
        # 1. Uncached
        start = time.time()
        generate_action_reply("hello")
        uncached_time = time.time() - start

        # 2. Cached
        start = time.time()
        for _ in range(100):
            generate_action_reply("hello")
        cached_avg = (time.time() - start) / 100

        print(f"\nLLM - Uncached: {uncached_time:.6f}s, Cached avg: {cached_avg:.6f}s")
        assert cached_avg < uncached_time

def test_elevenlabs_performance():
    from backend.app.services.elevenlabs_service import synthesize_speech, _get_cached_speech, _get_cached_client

    # Clear caches
    _get_cached_speech.cache_clear()
    _get_cached_client.cache_clear()

    mock_client = MagicMock()
    # ElevenLabs client call returns a generator/stream
    mock_client.text_to_speech.convert.return_value = [b"audio_data"]

    with patch('backend.app.services.elevenlabs_service.ElevenLabs', return_value=mock_client):
        # 1. Uncached
        start = time.time()
        synthesize_speech("hello")
        uncached_time = time.time() - start

        # 2. Cached
        start = time.time()
        for _ in range(100):
            synthesize_speech("hello")
        cached_avg = (time.time() - start) / 100

        print(f"ElevenLabs - Uncached: {uncached_time:.6f}s, Cached avg: {cached_avg:.6f}s")
        assert cached_avg < uncached_time

if __name__ == "__main__":
    pytest.main([__file__])
