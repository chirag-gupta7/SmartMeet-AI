import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import inspect

from backend.app import create_app, db
from backend.app.config import Config
from backend.app.services.elevenlabs_service import (
    synthesize_speech,
    _synthesize_speech_memoized,
)
from backend.app.services.llm_service import (
    generate_action_reply,
    _get_llm_response_memoized,
)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    HUGGINGFACE_API_KEY = "test-hf-key"
    ELEVENLABS_API_KEY = "test-elevenlabs-key"


@pytest.fixture
def app():
    app_instance = create_app(TestConfig)
    with app_instance.app_context():
        # Clean caches for test isolation
        _synthesize_speech_memoized.cache_clear()
        _get_llm_response_memoized.cache_clear()
        yield app_instance


@pytest.fixture
def client(app):
    return app.test_client()


def test_database_indices(app):
    """Verify that Meeting model has indices on owner_id and start_time."""
    with app.app_context():
        inspector = inspect(db.engine)
        indexes = inspector.get_indexes("meetings")
        column_names = []
        for idx in indexes:
            column_names.extend(idx["column_names"])

        assert "owner_id" in column_names
        assert "start_time" in column_names


@patch("backend.app.services.elevenlabs_service.ElevenLabs")
def test_elevenlabs_singleton_and_memoization(mock_elevenlabs_class, app):
    """Test singleton client reuse and lru_cache for ElevenLabs TTS."""
    mock_client_instance = MagicMock()
    mock_elevenlabs_class.return_value = mock_client_instance
    mock_client_instance.text_to_speech.convert.return_value = [b"audio"]

    # Reset global state for the test
    import backend.app.services.elevenlabs_service as el_service
    el_service._client = None
    el_service._last_api_key = None
    _synthesize_speech_memoized.cache_clear()

    with app.app_context():
        # First call: initializes client and converts speech
        res1 = synthesize_speech("Hello")
        assert res1 is not None
        assert mock_elevenlabs_class.call_count == 1
        assert mock_client_instance.text_to_speech.convert.call_count == 1

        # Second call: same text, hits the cache
        res2 = synthesize_speech("Hello")
        assert res2 == res1
        assert mock_elevenlabs_class.call_count == 1
        assert mock_client_instance.text_to_speech.convert.call_count == 1

        # Third call: different text, bypasses cache, but reuses client
        res3 = synthesize_speech("World")
        assert res3 is not None
        assert mock_elevenlabs_class.call_count == 1
        assert mock_client_instance.text_to_speech.convert.call_count == 2


@patch("backend.app.services.llm_service.InferenceClient")
def test_llm_singleton_and_memoization(mock_hf_class, app):
    """Test singleton client reuse and lru_cache for HF LLM."""
    mock_client_instance = MagicMock()
    mock_hf_class.return_value = mock_client_instance

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"action": "weather", "reply": "Sunny"}'
            )
        )
    ]
    mock_client_instance.chat_completion.return_value = mock_response

    # Reset global state for the test
    import backend.app.services.llm_service as llm_service
    llm_service._client = None
    llm_service._last_api_key = None
    _get_llm_response_memoized.cache_clear()

    with app.app_context():
        # First call: initializes client and completions
        action1, reply1 = generate_action_reply("weather")
        assert action1 == "weather"
        assert mock_hf_class.call_count == 1
        assert mock_client_instance.chat_completion.call_count == 1

        # Second call: same query, hits cache
        action2, reply2 = generate_action_reply("weather")
        assert action2 == "weather"
        assert mock_hf_class.call_count == 1
        assert mock_client_instance.chat_completion.call_count == 1

        # Third call: different query, bypasses cache, reuses client
        action3, reply3 = generate_action_reply("What is the weather today?")
        assert action3 == "weather"
        assert mock_hf_class.call_count == 1
        assert mock_client_instance.chat_completion.call_count == 2
