import base64
import logging
from functools import lru_cache
from typing import Dict, Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Cache for ElevenLabs client instances to avoid repeated initialization overhead
_client_cache: Dict[str, ElevenLabs] = {}


def _get_client(api_key: str) -> Optional[ElevenLabs]:
    """Get or create a cached ElevenLabs client."""
    if api_key not in _client_cache:
        try:
            _client_cache[api_key] = ElevenLabs(api_key=api_key)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            return None
    return _client_cache[api_key]


@lru_cache(maxsize=128)
def _synthesize_speech_memoized(api_key: str, voice_id: str, text: str) -> str:
    """
    Internal memoized function to perform the actual synthesis.
    Results are cached based on the API key, voice ID, and text content.
    Raises Exception on failure to avoid caching error states.
    """
    client = _get_client(api_key)
    if not client:
        raise RuntimeError("ElevenLabs client could not be initialized")

    # BOLT OPTIMIZATION: Memoization prevents redundant expensive API calls
    # and reduces latency for common phrases like greetings from ~1s to ~1ms.
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
    Uses memoization to cache results of frequent requests.
    """
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        return None

    voice_id = current_app.config.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

    try:
        return _synthesize_speech_memoized(api_key, voice_id, text)
    except Exception as exc:  # pylint: disable=broad-except
        # Log failure but return None so callers can fallback to text-only.
        # Exceptions are not cached by lru_cache, allowing retry on next call.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
