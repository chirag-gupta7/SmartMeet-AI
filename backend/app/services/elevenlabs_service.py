import base64
import logging
from functools import lru_cache
from typing import Optional

from elevenlabs import ElevenLabs
from flask import current_app

logger = logging.getLogger(__name__)

_client = None
_last_api_key = None


def _get_client(api_key: Optional[str] = None) -> Optional[ElevenLabs]:
    """Retrieve or initialize the ElevenLabs singleton client."""
    global _client, _last_api_key
    if not api_key:
        api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    if _client is None or api_key != _last_api_key:
        try:
            _client = ElevenLabs(api_key=api_key)
            _last_api_key = api_key
            logger.info("Initialized new ElevenLabs singleton client")
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _client


@lru_cache(maxsize=128)
def _synthesize_speech_memoized(
    text: str, api_key: str, voice_id: str
) -> str:
    """Helper for memoizing TTS synthesis. Raises exceptions on failure."""
    client = _get_client(api_key)
    if not client:
        raise ValueError("ElevenLabs client could not be initialized")

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
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    try:
        return _synthesize_speech_memoized(text, api_key, voice_id)
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
