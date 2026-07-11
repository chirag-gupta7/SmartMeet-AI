import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Singleton client storage
_client = None
_last_api_key = None


def _get_client() -> Optional[ElevenLabs]:
    """Returns a singleton ElevenLabs client."""
    global _client, _last_api_key
    api_key = current_app.config.get("ELEVENLABS_API_KEY")

    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    # Re-initialize if API key changed or client is None
    if _client is None or api_key != _last_api_key:
        try:
            _client = ElevenLabs(api_key=api_key)
            _last_api_key = api_key
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None

    return _client


@lru_cache(maxsize=128)
def _memoized_synthesize(api_key: str, voice_id: str, text: str) -> str:
    """
    Internal cached synthesis.
    api_key is included in the cache key to ensure config-sensitivity.
    We raise exceptions for failures to avoid caching them.
    """
    client = _get_client()
    if not client:
        raise RuntimeError("ElevenLabs client not available")

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    audio_bytes = b"".join(audio_stream)
    return base64.b64encode(audio_bytes).decode("utf-8")


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        return None

    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    try:
        return _memoized_synthesize(api_key, voice_id, text)
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        # Exceptions are NOT cached by lru_cache.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
