import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Cache for the ElevenLabs client instance
_elevenlabs_client: Optional[ElevenLabs] = None


def _get_client() -> Optional[ElevenLabs]:
    global _elevenlabs_client
    if _elevenlabs_client is not None:
        return _elevenlabs_client

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None
    try:
        _elevenlabs_client = ElevenLabs(api_key=api_key)
        return _elevenlabs_client
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to init ElevenLabs client: %s", exc)
        return None


@lru_cache(maxsize=64)
def _memoized_synthesize(text: str, voice_id: str, api_key: str) -> bytes:
    """
    Perform the actual TTS API call and cache results.
    API key is included in arguments to ensure cache invalidation if key changes.
    """
    client = ElevenLabs(api_key=api_key)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    return b"".join(audio_stream)


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        return None

    voice_id = current_app.config.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

    try:
        # Use memoized helper to avoid redundant API calls for same text/voice
        audio_bytes = _memoized_synthesize(text, voice_id, api_key)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
