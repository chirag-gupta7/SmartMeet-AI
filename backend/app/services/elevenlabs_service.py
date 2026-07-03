import base64
import functools
import logging
from typing import Optional, Dict

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Global client cache to avoid recreating ElevenLabs client instance
_eleven_clients_cache: Dict[str, ElevenLabs] = {}


def _get_client(api_key: str) -> Optional[ElevenLabs]:
    """Retrieves or creates a cached ElevenLabs client."""
    if api_key not in _eleven_clients_cache:
        try:
            _eleven_clients_cache[api_key] = ElevenLabs(api_key=api_key)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _eleven_clients_cache[api_key]


@functools.lru_cache(maxsize=128)
def _memoized_synthesize_speech(
    text: str, api_key: str, voice_id: str
) -> Optional[str]:
    """Internal memoized TTS call to reduce redundant API requests."""
    client = _get_client(api_key)
    if not client:
        return None

    # Note: Exceptions are NOT caught here to avoid caching failure states
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
    )
    audio_bytes = b"".join(audio_stream)
    return base64.b64encode(audio_bytes).decode("utf-8")


def synthesize_speech(text: str) -> Optional[str]:
    """
    Convert text to base64-encoded audio using ElevenLabs.
    Optimized with client caching and result memoization.
    """
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
        # Wrap the memoized call to handle transient API failures
        # without caching them
        return _memoized_synthesize_speech(text, api_key, voice_id)
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
