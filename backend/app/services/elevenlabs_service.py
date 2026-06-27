import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_cached_client(api_key: str) -> ElevenLabs:
    """Returns a memoized ElevenLabs client."""
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
def _memoized_synthesize(api_key: str, voice_id: str, text: str) -> bytes:
    """
    Internal memoized function for TTS synthesis.
    We pass api_key and voice_id to ensure cache invalidation if they change.
    """
    client = _get_cached_client(api_key)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    return b"".join(audio_stream)


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs (with caching)."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    voice_id = current_app.config.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

    if not api_key:
        return None

    try:
        # We use a memoized helper to avoid redundant API calls for the same text
        audio_bytes = _memoized_synthesize(api_key, voice_id, text)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        # Note: Exceptions are NOT cached by lru_cache, which is desired.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
