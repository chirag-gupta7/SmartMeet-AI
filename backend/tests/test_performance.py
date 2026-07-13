
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services.llm_service import (
    generate_action_reply, _get_llm_response_memoized, _client as llm_client
)
from backend.app.services.elevenlabs_service import (
    synthesize_speech, _synthesize_speech_memoized, _client as el_client
)
import backend.app.services.llm_service as llm_service
import backend.app.services.elevenlabs_service as el_service

@pytest.fixture(autouse=True)
def reset_globals():
    # Reset singleton clients
    llm_service._client = None
    llm_service._last_api_key = None
    el_service._client = None
    el_service._last_api_key = None
    # Clear caches
    _get_llm_response_memoized.cache_clear()
    _synthesize_speech_memoized.cache_clear()

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['HUGGINGFACE_API_KEY'] = 'fake-hf-key'
    app.config['ELEVENLABS_API_KEY'] = 'fake-el-key'
    app.config['ELEVENLABS_VOICE_ID'] = 'fake-voice'
    return app

def test_llm_optimization(app):
    with app.app_context():
        with patch('backend.app.services.llm_service.InferenceClient') as MockClient:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '{"action": "general_response", "reply": "hello"}'
            MockClient.return_value.chat_completion.return_value = mock_response

            # First call: instantiates client and calls API
            generate_action_reply("hello")
            assert MockClient.call_count == 1
            assert MockClient.return_value.chat_completion.call_count == 1

            # Second call (same input): uses cache, no client instantiation, no API call
            generate_action_reply("hello")
            assert MockClient.call_count == 1
            assert MockClient.return_value.chat_completion.call_count == 1

            # Third call (different input): uses same client, calls API
            generate_action_reply("different")
            assert MockClient.call_count == 1
            assert MockClient.return_value.chat_completion.call_count == 2

def test_elevenlabs_optimization(app):
    with app.app_context():
        with patch('backend.app.services.elevenlabs_service.ElevenLabs') as MockClient:
            MockClient.return_value.text_to_speech.convert.return_value = [b"audio"]

            # First call: instantiates client and calls API
            synthesize_speech("hello")
            assert MockClient.call_count == 1
            assert MockClient.return_value.text_to_speech.convert.call_count == 1

            # Second call (same input): uses cache
            synthesize_speech("hello")
            assert MockClient.call_count == 1
            assert MockClient.return_value.text_to_speech.convert.call_count == 1

            # Third call (different input): uses same client, calls API
            synthesize_speech("different")
            assert MockClient.call_count == 1
            assert MockClient.return_value.text_to_speech.convert.call_count == 2

def test_api_key_change_reinstantiates_client(app):
    with app.app_context():
        with patch('backend.app.services.llm_service.InferenceClient') as MockClient:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '{"action": "test", "reply": "hi"}'
            MockClient.return_value.chat_completion.return_value = mock_response

            # First call
            generate_action_reply("hello")
            assert MockClient.call_count == 1

            # Change API key
            app.config['HUGGINGFACE_API_KEY'] = 'new-key'

            # Second call: should re-instantiate client because API key changed
            generate_action_reply("hello again")
            assert MockClient.call_count == 2
