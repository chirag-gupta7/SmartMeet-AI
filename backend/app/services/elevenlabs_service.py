import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Global cache for the ElevenLabs client instance
_client_cache = {}


def _get_client() -> Optional[ElevenLabs]:
    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    # Cache client instance by API key to avoid re-initialization
    if api_key not in _client_cache:
        try:
            _client_cache[api_key] = ElevenLabs(api_key=api_key)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _client_cache[api_key]


@lru_cache(maxsize=100)
def _memoized_synthesize(text: str, voice_id: str, api_key: str) -> str:
    """Internal memoized function to perform the actual TTS conversion."""
    # Retrieve or create cached client
    if api_key not in _client_cache:
        _client_cache[api_key] = ElevenLabs(api_key=api_key)
    client = _client_cache[api_key]

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    audio_bytes = b"".join(audio_stream)
    return base64.b64encode(audio_bytes).decode("utf-8")


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs (with caching)."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        return None

    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    try:
        # Use memoized helper to avoid redundant API calls for same text.
        # Exceptions are not cached by lru_cache, allowing retries.
        return _memoized_synthesize(text, voice_id, api_key)
    except Exception as exc:
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
