import base64
import logging
from typing import Optional
from functools import lru_cache

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_cached_client(api_key: str) -> ElevenLabs:
    """Cache the ElevenLabs client instance."""
    return ElevenLabs(api_key=api_key)


def _get_client() -> Optional[ElevenLabs]:
    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None
    try:
        return _get_cached_client(api_key)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to init ElevenLabs client: %s", exc)
        return None


@lru_cache(maxsize=128)
def _get_cached_speech(api_key: str, voice_id: str, text: str) -> Optional[str]:
    """Internal function to cache TTS results."""
    client = _get_cached_client(api_key)

    # elevenlabs client can raise exceptions, which we should let bubble up
    # to the caller so they are NOT cached.
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

    voice_id = current_app.config.get("ELEVENLABS_VOICE_ID",
                                      "pNInz6obpgDQGcFmaJgB")

    try:
        return _get_cached_speech(api_key, voice_id, text)
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
