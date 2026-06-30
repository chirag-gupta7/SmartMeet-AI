import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Cache for ElevenLabs client instances
_client_cache = {}


def _get_client(api_key: str) -> Optional[ElevenLabs]:
    """Get or create a cached ElevenLabs client instance."""
    if api_key not in _client_cache:
        try:
            _client_cache[api_key] = ElevenLabs(api_key=api_key)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _client_cache[api_key]


@lru_cache(maxsize=128)
def _memoized_synthesize_speech(text: str, api_key: str, voice_id: str) -> str:
    """Internal memoized function for TTS.

    Raises exceptions on failure to avoid caching error states.
    """
    client = _get_client(api_key)
    if not client:
        raise RuntimeError("ElevenLabs client could not be initialized")

    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
        )
        audio_bytes = b"".join(audio_stream)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        raise exc


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs.

    Optimized with client caching and result memoization.
    """
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    try:
        return _memoized_synthesize_speech(text, api_key, voice_id)
    except Exception:
        # Fallback for memoization failures
        return None


__all__ = ["synthesize_speech"]
