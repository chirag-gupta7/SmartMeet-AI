import time
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

# Import services
from app.services import llm_service, elevenlabs_service

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['HUGGINGFACE_API_KEY'] = 'fake-hf-key'
    app.config['ELEVENLABS_API_KEY'] = 'fake-eleven-key'
    return app

def test_llm_service_performance(app):
    with app.app_context():
        # Mock the client to simulate a delay
        with patch('app.services.llm_service.InferenceClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock the chat_completion to return a fixed JSON response with delay
            def slow_response(*args, **kwargs):
                time.sleep(0.5) # Simulate 500ms API delay
                mock_res = MagicMock()
                mock_res.choices[0].message.content = '{"action": "general_response", "reply": "Hello!"}'
                return mock_res

            mock_client.chat_completion.side_effect = slow_response

            # First call (Miss)
            start = time.time()
            llm_service.generate_action_reply("Hello")
            first_duration = time.time() - start

            # Second call (Hit)
            start = time.time()
            llm_service.generate_action_reply("Hello")
            second_duration = time.time() - start

            print(f"\nLLM First call: {first_duration:.4f}s")
            print(f"LLM Second call: {second_duration:.4f}s")

            # First call should be around 0.5s, second should be near 0
            assert first_duration >= 0.5
            assert second_duration < 0.01


def test_elevenlabs_service_performance(app):
    with app.app_context():
        with patch('app.services.elevenlabs_service.ElevenLabs') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            def slow_audio(*args, **kwargs):
                time.sleep(0.5) # Simulate 500ms API delay
                return [b"fake", b"audio", b"data"]

            mock_client.text_to_speech.convert.side_effect = slow_audio

            # First call
            start = time.time()
            elevenlabs_service.synthesize_speech("Greeting")
            first_duration = time.time() - start

            # Second call
            start = time.time()
            elevenlabs_service.synthesize_speech("Greeting")
            second_duration = time.time() - start

            print(f"\nTTS First call: {first_duration:.4f}s")
            print(f"TTS Second call: {second_duration:.4f}s")

            # Assert that the second call is significantly faster (cached)
            assert first_duration >= 0.5
            assert second_duration < 0.01
