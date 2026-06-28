import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Cache for ElevenLabs client to avoid repeated initializations
_client_cache = {}


def _get_client(api_key: str) -> Optional[ElevenLabs]:
    """Get or create a cached ElevenLabs client."""
    if api_key in _client_cache:
        return _client_cache[api_key]

    try:
        client = ElevenLabs(api_key=api_key)
        _client_cache[api_key] = client
        return client
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to init ElevenLabs client: %s", exc)
        return None


@lru_cache(maxsize=128)
def _memoized_synthesize(text: str, api_key: str, voice_id: str) -> \
        Optional[str]:
    """Internal memoized function for speech synthesis."""
    client = _get_client(api_key)
    if not client:
        # We don't want to cache failure due to missing client
        raise RuntimeError("ElevenLabs client not available")

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    audio_bytes = b"".join(audio_stream)
    return base64.b64encode(audio_bytes).decode("utf-8")


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs with caching."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    v_id = current_app.config.get("ELEVENLABS_VOICE_ID",
                                  "pNInz6obpgDQGcFmaJgB")

    try:
        # Use memoized internal function to benefit from lru_cache
        # We pass config values to ensure cache is invalidated if they change
        return _memoized_synthesize(text, api_key, v_id)
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
