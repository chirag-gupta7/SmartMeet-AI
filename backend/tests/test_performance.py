import pytest

from backend.app import create_app, db
from backend.app.config import Config
from backend.app.services import elevenlabs_service, llm_service
from backend.app.services.elevenlabs_service import synthesize_speech
from backend.app.services.llm_service import generate_action_reply


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    HUGGINGFACE_API_KEY = "test_hf_key"
    ELEVENLABS_API_KEY = "test_elevenlabs_key"
    ELEVENLABS_VOICE_ID = "test_voice"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def clear_caches():
    # Reset singleton LLM client and clear memoization cache
    llm_service._get_llm_response_memoized.cache_clear()
    llm_service._client = None
    llm_service._last_api_key = None

    # Reset singleton ElevenLabs client and clear memoization cache
    elevenlabs_service._synthesize_speech_memoized.cache_clear()
    elevenlabs_service._client = None
    elevenlabs_service._last_api_key = None


@pytest.fixture
def mock_hf_client(mocker):
    mock_class = mocker.patch(
        "backend.app.services.llm_service.InferenceClient"
    )
    mock_instance = mocker.Mock()
    mock_class.return_value = mock_instance

    # Mock choices in response
    mock_msg = mocker.Mock()
    mock_msg.content = '{"action": "weather", "reply": "Sunny!"}'
    mock_choice = mocker.Mock()
    mock_choice.message = mock_msg
    mock_response = mocker.Mock()
    mock_response.choices = [mock_choice]

    mock_instance.chat_completion.return_value = mock_response
    return mock_instance


@pytest.fixture
def mock_elevenlabs_client(mocker):
    mock_class = mocker.patch(
        "backend.app.services.elevenlabs_service.ElevenLabs"
    )
    mock_instance = mocker.Mock()
    mock_class.return_value = mock_instance

    # Mock text_to_speech.convert response
    mock_instance.text_to_speech.convert.return_value = [b"mock_audio_bytes"]
    return mock_instance


def test_llm_cache_hits(app, mock_hf_client, clear_caches):
    with app.app_context():
        # First call: should call the underlying API
        action, reply = generate_action_reply("What's the weather?")
        assert action == "weather"
        assert reply == "Sunny!"
        assert mock_hf_client.chat_completion.call_count == 1

        # Second call with same text: should NOT call API again (cache hit)
        action2, reply2 = generate_action_reply("What's the weather?")
        assert action2 == "weather"
        assert reply2 == "Sunny!"
        assert mock_hf_client.chat_completion.call_count == 1


def test_llm_cache_invalidation(app, mock_hf_client, clear_caches):
    with app.app_context():
        # First call with API key 1
        app.config["HUGGINGFACE_API_KEY"] = "key1"
        generate_action_reply("Hello")
        assert mock_hf_client.chat_completion.call_count == 1

        # Second call with same text, but API key 2 (should call API again)
        app.config["HUGGINGFACE_API_KEY"] = "key2"
        generate_action_reply("Hello")
        assert mock_hf_client.chat_completion.call_count == 2


def test_elevenlabs_cache_hits(app, mock_elevenlabs_client, clear_caches):
    with app.app_context():
        app.config["ELEVENLABS_API_KEY"] = "some_key"
        # First call
        audio1 = synthesize_speech("Hello")
        assert audio1 is not None
        assert mock_elevenlabs_client.text_to_speech.convert.call_count == 1

        # Second call (cache hit)
        audio2 = synthesize_speech("Hello")
        assert audio2 == audio1
        assert mock_elevenlabs_client.text_to_speech.convert.call_count == 1


def test_elevenlabs_cache_invalidation(
    app, mock_elevenlabs_client, clear_caches
):
    with app.app_context():
        app.config["ELEVENLABS_API_KEY"] = "key1"
        synthesize_speech("Hello")
        assert mock_elevenlabs_client.text_to_speech.convert.call_count == 1

        # Change key: should invalidate cache and create new client
        app.config["ELEVENLABS_API_KEY"] = "key2"
        synthesize_speech("Hello")
        assert mock_elevenlabs_client.text_to_speech.convert.call_count == 2


def test_elevenlabs_voice_invalidation(
    app, mock_elevenlabs_client, clear_caches
):
    with app.app_context():
        app.config["ELEVENLABS_API_KEY"] = "some_key"
        app.config["ELEVENLABS_VOICE_ID"] = "voice1"
        synthesize_speech("Hello")
        assert mock_elevenlabs_client.text_to_speech.convert.call_count == 1

        # Change voice ID: should invalidate cache and make a new call
        app.config["ELEVENLABS_VOICE_ID"] = "voice2"
        synthesize_speech("Hello")
        assert mock_elevenlabs_client.text_to_speech.convert.call_count == 2


def test_meeting_indices(app):
    with app.app_context():
        # Get metadata inspector
        from sqlalchemy import inspect

        inspector = inspect(db.engine)

        # Get indexes for 'meetings' table
        indexes = inspector.get_indexes("meetings")

        # We expect indexes on owner_id and start_time
        indexed_columns = []
        for index in indexes:
            indexed_columns.extend(index["column_names"])

        assert "owner_id" in indexed_columns
        assert "start_time" in indexed_columns
