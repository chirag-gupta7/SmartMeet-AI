import base64
import logging
from typing import Optional
from functools import lru_cache

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client(api_key: str) -> Optional[ElevenLabs]:
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None
    try:
        return ElevenLabs(api_key=api_key)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to init ElevenLabs client: %s", exc)
        return None


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    return _synthesize_speech_cached(text, api_key, voice_id)


@lru_cache(maxsize=100)
def _synthesize_speech_cached(text: str, api_key: str,
                              voice_id: str) -> Optional[str]:
    """
    Actual implementation of TTS with memoization.
    api_key and voice_id are passed to ensure cache invalidation if
    config changes.
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
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
