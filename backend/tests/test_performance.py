import time
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from backend.app.services.elevenlabs_service import synthesize_speech, _memoized_synthesize
from backend.app.services.llm_service import generate_action_reply, _memoized_generate

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['ELEVENLABS_API_KEY'] = 'fake_key'
    app.config['ELEVENLABS_VOICE_ID'] = 'fake_voice'
    app.config['HUGGINGFACE_API_KEY'] = 'fake_key'
    return app

def test_elevenlabs_performance(app):
    with app.app_context():
        # Clear cache if it exists (for reruns after optimization)
        if hasattr(_memoized_synthesize, 'cache_clear'):
            _memoized_synthesize.cache_clear()

        with patch('backend.app.services.elevenlabs_service.ElevenLabs') as mock_elevenlabs:
            mock_client = MagicMock()
            mock_elevenlabs.return_value = mock_client

            def slow_convert(*args, **kwargs):
                time.sleep(0.5)
                return [b"audio_data"]

            mock_client.text_to_speech.convert.side_effect = slow_convert

            start = time.time()
            synthesize_speech("Hello")
            first_duration = time.time() - start

            start = time.time()
            synthesize_speech("Hello")
            second_duration = time.time() - start

            print(f"\nElevenLabs - First call: {first_duration:.4f}s, Second call: {second_duration:.4f}s")
            assert first_duration >= 0.5
            # Before optimization, this will fail as it will take another 0.5s
            assert second_duration < 0.1, f"Second call too slow: {second_duration:.4f}s"

def test_llm_performance(app):
    with app.app_context():
        # Clear cache if it exists
        if hasattr(_memoized_generate, 'cache_clear'):
            _memoized_generate.cache_clear()

        with patch('backend.app.services.llm_service.InferenceClient') as mock_hf:
            mock_client = MagicMock()
            mock_hf.return_value = mock_client

            def slow_chat(*args, **kwargs):
                time.sleep(0.5)
                mock_response = MagicMock()
                mock_response.choices[0].message.content = '{"action": "general_response", "reply": "hi"}'
                return mock_response

            mock_client.chat_completion.side_effect = slow_chat

            start = time.time()
            generate_action_reply("Hi")
            first_duration = time.time() - start

            start = time.time()
            generate_action_reply("Hi")
            second_duration = time.time() - start

            print(f"\nLLM - First call: {first_duration:.4f}s, Second call: {second_duration:.4f}s")
            assert first_duration >= 0.5
            # Before optimization, this will fail as it will take another 0.5s
            assert second_duration < 0.1, f"Second call too slow: {second_duration:.4f}s"
