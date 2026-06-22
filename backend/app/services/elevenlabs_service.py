import base64
import logging
from typing import Optional
from functools import lru_cache

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Cache for the ElevenLabs client instance to avoid repeated initialization
_client_cache = None


def _get_client() -> Optional[ElevenLabs]:
    global _client_cache
    if _client_cache is not None:
        return _client_cache

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None
    try:
        _client_cache = ElevenLabs(api_key=api_key)
        return _client_cache
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to init ElevenLabs client: %s", exc)
        return None


@lru_cache(maxsize=128)
def _memoized_synthesize_speech(
    text: str, voice_id: str, api_key: Optional[str]
) -> str:
    """
    Internal memoized function for TTS.
    We include api_key in the signature to ensure cache invalidation if the
    key changes, even though _get_client handles the actual client retrieval.
    """
    client = _get_client()
    if not client:
        raise RuntimeError("ElevenLabs client not available")

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    audio_bytes = b"".join(audio_stream)
    return base64.b64encode(audio_bytes).decode("utf-8")


def synthesize_speech(text: str) -> Optional[str]:
    """
    Convert text to base64-encoded audio using ElevenLabs
    with result memoization.
    """
    if not text:
        return None

    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )
    api_key = current_app.config.get("ELEVENLABS_API_KEY")

    try:
        # Using a wrapper to avoid caching failure states (exceptions)
        return _memoized_synthesize_speech(text, voice_id, api_key)
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
