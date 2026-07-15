import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Singleton client and its config tracking
_client = None
_last_api_key = None


def _get_client() -> Optional[ElevenLabs]:
    """
    Get or create a singleton ElevenLabs client.
    Optimization: Reuses the same client instance across requests, reducing
    instantiation overhead.
    """
    global _client, _last_api_key
    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    if _client is None or api_key != _last_api_key:
        try:
            _client = ElevenLabs(api_key=api_key)
            _last_api_key = api_key
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _client


@lru_cache(maxsize=100)
def _synthesize_speech_memoized(
    api_key: str, voice_id: str, text: str
) -> Optional[str]:
    """
    Memoized helper for speech synthesis.
    API key and voice ID are included in arguments to ensure cache validity.
    Performance: Reduces response time for repeated TTS from ~1-3s
    to <1ms by caching base64 audio.
    """
    client = _get_client()
    if not client:
        raise ValueError("ElevenLabs client could not be initialized")

    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
        )
        audio_bytes = b"".join(audio_stream)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        # We don't want to cache failure states.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        raise exc


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
        # Use memoized helper to avoid redundant API calls for same text/voice
        return _synthesize_speech_memoized(api_key, voice_id, text)
    except Exception:
        # Return None so callers can still show text; log for visibility.
        return None


__all__ = ["synthesize_speech"]
