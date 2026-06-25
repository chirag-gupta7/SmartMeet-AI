import time
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services.llm_service import generate_action_reply
from backend.app.services.elevenlabs_service import synthesize_speech

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['HUGGINGFACE_API_KEY'] = 'fake_hf_key'
    app.config['ELEVENLABS_API_KEY'] = 'fake_el_key'
    return app

def test_llm_service_performance(app):
    with app.app_context():
        # Mocking the InferenceClient and its chat_completion method
        with patch('backend.app.services.llm_service.InferenceClient') as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.chat_completion.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"action": "test", "reply": "hello"}'))]
            )

            # First call (unmemoized)
            start_time = time.perf_counter()
            generate_action_reply("hello")
            end_time = time.perf_counter()
            initial_duration = end_time - start_time

            # Subsequent calls (should be faster after optimization)
            start_time = time.perf_counter()
            for _ in range(10):
                generate_action_reply("hello")
            end_time = time.perf_counter()
            subsequent_duration = (end_time - start_time) / 10

            print(f"\nLLM Service - Initial: {initial_duration:.6f}s, Subsequent average: {subsequent_duration:.6f}s")

def test_tts_service_performance(app):
    with app.app_context():
        # Mocking ElevenLabs client and its convert method
        with patch('backend.app.services.elevenlabs_service.ElevenLabs') as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.text_to_speech.convert.return_value = [b"fake_audio_chunk"]

            # First call
            start_time = time.perf_counter()
            synthesize_speech("hello")
            end_time = time.perf_counter()
            initial_duration = end_time - start_time

            # Subsequent calls
            start_time = time.perf_counter()
            for _ in range(10):
                synthesize_speech("hello")
            end_time = time.perf_counter()
            subsequent_duration = (end_time - start_time) / 10

            print(f"\nTTS Service - Initial: {initial_duration:.6f}s, Subsequent average: {subsequent_duration:.6f}s")
