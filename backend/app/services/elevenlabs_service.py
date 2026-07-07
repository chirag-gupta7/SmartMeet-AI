import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_cached_client(api_key: str) -> Optional[ElevenLabs]:
    """Cache the ElevenLabs client instance."""
    try:
        return ElevenLabs(api_key=api_key)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to init ElevenLabs client: %s", exc)
        return None


def _get_client() -> Optional[ElevenLabs]:
    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None
    return _get_cached_client(api_key)


@lru_cache(maxsize=100)
def _synthesize_speech_memoized(
    text: str, api_key: str, voice_id: str
) -> str:
    """Memoize the TTS response to avoid redundant API calls."""
    client = _get_cached_client(api_key)
    if not client:
        raise RuntimeError("ElevenLabs client not available")

    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
        )
        audio_bytes = b"".join(audio_stream)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        # Do not cache failure states
        raise exc


def synthesize_speech(text: str) -> Optional[str]:
    """
    Convert text to base64-encoded audio using ElevenLabs.
    Uses memoization to avoid redundant calls.
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
        return _synthesize_speech_memoized(text, api_key, voice_id)
    except Exception:
        # Return None so callers can still show text
        return None


__all__ = ["synthesize_speech"]
