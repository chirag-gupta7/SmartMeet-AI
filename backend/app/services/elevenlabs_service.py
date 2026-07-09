import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Global cache for the ElevenLabs client instance
_client = None
_last_api_key = None


def _get_client(api_key: str) -> Optional[ElevenLabs]:
    """Retrieves or initializes the ElevenLabs client."""
    global _client, _last_api_key
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    if _client is None or api_key != _last_api_key:
        try:
            _client = ElevenLabs(api_key=api_key)
            _last_api_key = api_key
        except Exception as exc:
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _client


@lru_cache(maxsize=128)
def _synthesize_cached(
    text: str, api_key: str, voice_id: str
) -> Optional[str]:
    """
    Internal memoized synthesis function.
    Passing api_key/voice_id ensures cache invalidation on config changes.
    """
    client = _get_client(api_key)
    if not client:
        return None

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
        # Raise to avoid caching failure state in lru_cache
        raise exc


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio with caching."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    try:
        return _synthesize_cached(text, api_key, voice_id)
    except Exception:
        # Fallback to None so the application can still display text
        return None


__all__ = ["synthesize_speech"]
