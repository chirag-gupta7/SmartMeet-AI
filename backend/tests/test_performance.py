import pytest
from unittest.mock import MagicMock, patch

from flask import Flask
from app.models import Meeting
from app.services import elevenlabs_service, llm_service
from app.services.elevenlabs_service import (
    _synthesize_speech_memoized,
    synthesize_speech,
)
from app.services.llm_service import (
    _get_llm_response_memoized,
    generate_action_reply,
)


@pytest.fixture(autouse=True)
def clear_caches():
    """Fixture to ensure test isolation by clearing lru_caches."""
    _synthesize_speech_memoized.cache_clear()
    _get_llm_response_memoized.cache_clear()
    yield
    _synthesize_speech_memoized.cache_clear()
    _get_llm_response_memoized.cache_clear()


@pytest.fixture(autouse=True)
def reset_singletons():
    """Fixture to reset singleton state variables before each test."""
    elevenlabs_service._client = None
    elevenlabs_service._last_api_key = None
    llm_service._client = None
    llm_service._last_api_key = None
    yield
    elevenlabs_service._client = None
    elevenlabs_service._last_api_key = None
    llm_service._client = None
    llm_service._last_api_key = None


@pytest.fixture
def test_app():
    """Create a minimal Flask app for testing services."""
    app = Flask("test_app")
    app.config["ELEVENLABS_API_KEY"] = "fake-elevenlabs-key"
    app.config["HUGGINGFACE_API_KEY"] = "fake-huggingface-key"
    return app


def test_elevenlabs_singleton_client(test_app):
    """Test ElevenLabs client singleton and key change re-init."""
    with test_app.app_context():
        # First call creates the client
        with patch("app.services.elevenlabs_service.ElevenLabs") as mock_class:
            mock_inst1 = MagicMock()
            mock_class.return_value = mock_inst1

            client1 = elevenlabs_service._get_client()
            assert client1 == mock_inst1
            mock_class.assert_called_once_with(api_key="fake-elevenlabs-key")

            # Second call returns cached singleton client without re-creating
            client2 = elevenlabs_service._get_client()
            assert client2 == mock_inst1
            assert mock_class.call_count == 1

        # Changing API key recreates the client
        test_app.config["ELEVENLABS_API_KEY"] = "new-elevenlabs-key"
        with patch("app.services.elevenlabs_service.ElevenLabs") as mock_class:
            mock_inst2 = MagicMock()
            mock_class.return_value = mock_inst2

            client3 = elevenlabs_service._get_client()
            assert client3 == mock_inst2
            mock_class.assert_called_once_with(api_key="new-elevenlabs-key")


def test_llm_singleton_client(test_app):
    """Test InferenceClient singleton and key change re-init."""
    with test_app.app_context():
        # First call creates the client
        with patch(
            "app.services.llm_service.InferenceClient"
        ) as mock_class:
            mock_inst1 = MagicMock()
            mock_class.return_value = mock_inst1

            client1 = llm_service._get_client()
            assert client1 == mock_inst1
            mock_class.assert_called_once_with(token="fake-huggingface-key")

            # Second call returns cached singleton client without re-creating
            client2 = llm_service._get_client()
            assert client2 == mock_inst1
            assert mock_class.call_count == 1

        # Changing API key recreates the client
        test_app.config["HUGGINGFACE_API_KEY"] = "new-huggingface-key"
        with patch(
            "app.services.llm_service.InferenceClient"
        ) as mock_class:
            mock_inst2 = MagicMock()
            mock_class.return_value = mock_inst2

            client3 = llm_service._get_client()
            assert client3 == mock_inst2
            mock_class.assert_called_once_with(token="new-huggingface-key")


def test_elevenlabs_memoization(test_app):
    """Test synthesize_speech caching and key change invalidation."""
    with test_app.app_context():
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio_bytes_123"]

        with patch(
            "app.services.elevenlabs_service._get_client",
            return_value=mock_client,
        ):
            # First call - cache miss, converts audio
            res1 = synthesize_speech("Hello world")
            assert res1 is not None
            assert mock_client.text_to_speech.convert.call_count == 1

            # Second call - cache hit, returns cached without calling convert
            res2 = synthesize_speech("Hello world")
            assert res2 == res1
            assert mock_client.text_to_speech.convert.call_count == 1

            # Third call with different text - cache miss, converts audio
            res3 = synthesize_speech("Different text")
            assert res3 is not None
            assert mock_client.text_to_speech.convert.call_count == 2

        # Changing API key should bypass/invalidate cache because key is arg
        test_app.config["ELEVENLABS_API_KEY"] = "another-key"
        with patch(
            "app.services.elevenlabs_service._get_client",
            return_value=mock_client,
        ):
            res4 = synthesize_speech("Hello world")
            assert res4 is not None
            assert mock_client.text_to_speech.convert.call_count == 3


def test_llm_memoization(test_app):
    """Test generate_action_reply caching and key change invalidation."""
    with test_app.app_context():
        mock_client = MagicMock()
        # Mocking the response choice message content
        mock_choice = MagicMock()
        mock_choice.message.content = (
            '{"action": "general_response", "reply": "Hi!"}'
        )
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_client.chat_completion.return_value = mock_resp

        with patch(
            "app.services.llm_service._get_client", return_value=mock_client
        ):
            # First call - cache miss, chat_completion called
            action1, reply1 = generate_action_reply("Hello LLM")
            assert action1 == "general_response"
            assert reply1 == "Hi!"
            assert mock_client.chat_completion.call_count == 1

            # Second call - cache hit, returns cached without calling LLM
            action2, reply2 = generate_action_reply("Hello LLM")
            assert action2 == "general_response"
            assert reply2 == "Hi!"
            assert mock_client.chat_completion.call_count == 1

            # Third call with different text - cache miss
            action3, reply3 = generate_action_reply("Different query")
            assert mock_client.chat_completion.call_count == 2

        # Changing API key should invalidate cache
        test_app.config["HUGGINGFACE_API_KEY"] = "another-key"
        with patch(
            "app.services.llm_service._get_client", return_value=mock_client
        ):
            action4, reply4 = generate_action_reply("Hello LLM")
            assert mock_client.chat_completion.call_count == 3


def test_database_indices():
    """Verify Meeting model has explicit indices on owner_id & start_time."""
    # owner_id column check
    owner_id_col = Meeting.__table__.columns.get("owner_id")
    assert owner_id_col is not None
    assert owner_id_col.index is True

    # start_time column check
    start_time_col = Meeting.__table__.columns.get("start_time")
    assert start_time_col is not None
    assert start_time_col.index is True
