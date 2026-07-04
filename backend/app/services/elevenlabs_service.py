import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_cached_client(api_key: str) -> ElevenLabs:
    """
    Create and cache an ElevenLabs client instance.
    Caching the client avoids redundant network or setup overhead.
    """
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
def _memoized_synthesize(text: str, api_key: str, voice_id: str) -> bytes:
    """
    Internal memoized function to perform the TTS conversion.
    Raises exceptions on failure so that errors are not cached.
    """
    client = _get_cached_client(api_key)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    return b"".join(audio_stream)


def synthesize_speech(text: str) -> Optional[str]:
    """
    Convert text to base64-encoded audio using ElevenLabs.
    Optimized with client caching and result memoization.
    """
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    if not api_key:
        return None

    try:
        # Use memoized helper to avoid repeated API calls for the same text
        audio_bytes = _memoized_synthesize(text, api_key, voice_id)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
