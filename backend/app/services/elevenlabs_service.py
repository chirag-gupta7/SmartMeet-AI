import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Global client cache
_eleven_client: Optional[ElevenLabs] = None


def _get_client() -> Optional[ElevenLabs]:
    global _eleven_client
    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    if _eleven_client is None:
        try:
            # Cache the client instance to avoid repeated initialization
            _eleven_client = ElevenLabs(api_key=api_key)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _eleven_client


@lru_cache(maxsize=64)
def _cached_synthesize_speech(
    text: str, api_key: str, voice_id: str
) -> Optional[str]:
    """Internal helper to memoize TTS results."""
    client = _get_client()
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
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


def synthesize_speech(text: str) -> Optional[str]:
    """
    Convert text to base64-encoded audio using ElevenLabs.
    Uses lru_cache via a helper to avoid redundant API calls.
    """
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        return None

    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    # Pass api_key and voice_id to the cached function to ensure cache validity
    return _cached_synthesize_speech(text, api_key, voice_id)


__all__ = ["synthesize_speech"]
