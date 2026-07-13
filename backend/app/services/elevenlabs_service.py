import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

_client: Optional[ElevenLabs] = None
_last_api_key: Optional[str] = None


def _get_client() -> Optional[ElevenLabs]:
    """Returns a singleton ElevenLabs client, re-initializing only if the
    API key changes.
    """
    global _client, _last_api_key
    api_key = current_app.config.get("ELEVENLABS_API_KEY")

    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        _client = None
        _last_api_key = None
        return None

    if _client is None or api_key != _last_api_key:
        try:
            _client = ElevenLabs(api_key=api_key)
            _last_api_key = api_key
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None

    return _client


@lru_cache(maxsize=64)
def _synthesize_speech_memoized(text: str, api_key: str, voice_id: str) -> str:
    """Helper for memoized TTS calls. api_key and voice_id are included
    in arguments to ensure cache validity during configuration changes.
    """
    client = _get_client()
    if not client:
        raise ValueError("TTS client not available")

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    audio_bytes = b"".join(audio_stream)
    return base64.b64encode(audio_bytes).decode("utf-8")


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using memoized ElevenLabs."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
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
