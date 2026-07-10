import time
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.app.services import llm_service

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['HUGGINGFACE_API_KEY'] = 'fake-key'
    return app

@pytest.fixture(autouse=True)
def reset_service_state():
    # Reset singleton
    llm_service._client = None
    # Clear cache
    llm_service._get_llm_response.cache_clear()
    yield

def test_llm_service_caching(app):
    with app.app_context():
        with patch('backend.app.services.llm_service.InferenceClient') as mock_client_class:
            mock_instance = mock_client_class.return_value
            mock_instance.chat_completion.return_value.choices = [
                MagicMock(message=MagicMock(content='{"action": "test", "reply": "hello"}'))
            ]

            # Call 1: Should instantiate client and call API
            start_time = time.time()
            llm_service.generate_action_reply("Hello")
            duration1 = time.time() - start_time

            assert mock_client_class.call_count == 1
            assert mock_instance.chat_completion.call_count == 1

            # Call 2: Same text, should use cache (no new instantiation, no new API call)
            start_time = time.time()
            llm_service.generate_action_reply("Hello")
            duration2 = time.time() - start_time

            assert mock_client_class.call_count == 1  # Still 1 (singleton)
            assert mock_instance.chat_completion.call_count == 1 # Still 1 (cache)
            assert duration2 < duration1

            # Call 3: Different text, should call API again but reuse client
            llm_service.generate_action_reply("World")
            assert mock_client_class.call_count == 1 # Still 1 (singleton)
            assert mock_instance.chat_completion.call_count == 2 # New call

def test_llm_service_error_not_cached(app):
    with app.app_context():
        with patch('backend.app.services.llm_service.InferenceClient') as mock_client_class:
            mock_instance = mock_client_class.return_value
            # First call fails
            mock_instance.chat_completion.side_effect = Exception("API Error")

            llm_service.generate_action_reply("Fail")
            assert mock_instance.chat_completion.call_count == 1

            # Second call with same text should try again (not cached)
            # This time it succeeds
            mock_instance.chat_completion.side_effect = None
            mock_instance.chat_completion.return_value.choices = [
                MagicMock(message=MagicMock(content='{"action": "test", "reply": "success"}'))
            ]

            action, reply = llm_service.generate_action_reply("Fail")
            assert mock_instance.chat_completion.call_count == 2
            assert action == "test"
            assert reply == "success"
