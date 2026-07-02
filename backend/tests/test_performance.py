import time
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services.elevenlabs_service import synthesize_speech
from backend.app.services.llm_service import generate_action_reply

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['ELEVENLABS_API_KEY'] = 'fake_key'
    app.config['HUGGINGFACE_API_KEY'] = 'fake_key'
    return app

def test_elevenlabs_performance(app, mocker):
    with app.app_context():
        # Mock ElevenLabs client and its convert method
        mock_client_class = mocker.patch('backend.app.services.elevenlabs_service.ElevenLabs')
        mock_client = mock_client_class.return_value
        mock_client.text_to_speech.convert.return_value = [b"audio_data"]

        text = "Hello, this is a test greeting."

        # First call
        start_time = time.time()
        res1 = synthesize_speech(text)
        duration1 = time.time() - start_time

        # Second call (identical text)
        start_time = time.time()
        res2 = synthesize_speech(text)
        duration2 = time.time() - start_time

        print(f"\nElevenLabs - Call 1: {duration1:.4f}s, Call 2: {duration2:.4f}s")

        assert res1 == res2
        # Before optimization, both calls should trigger the API mock
        # After optimization, Call 2 should be significantly faster and not call the mock

def test_llm_performance(app, mocker):
    with app.app_context():
        # Mock InferenceClient and its chat_completion method
        mock_client_class = mocker.patch('backend.app.services.llm_service.InferenceClient')
        mock_client = mock_client_class.return_value

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"action": "general_response", "reply": "Hello!"}'
        mock_client.chat_completion.return_value = mock_response

        text = "Hi there"

        # First call
        start_time = time.time()
        action1, reply1 = generate_action_reply(text)
        duration1 = time.time() - start_time

        # Second call (identical text)
        start_time = time.time()
        action2, reply2 = generate_action_reply(text)
        duration2 = time.time() - start_time

        print(f"\nLLM - Call 1: {duration1:.4f}s, Call 2: {duration2:.4f}s")

        assert action1 == action2
        assert reply1 == reply2
        # Similarly, Call 2 should be faster after optimization
