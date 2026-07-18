import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

# Global singleton client and its API key to detect changes
_client = None
_last_api_key = None


def _get_client() -> Optional[ElevenLabs]:
    global _client, _last_api_key
    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.info("ELEVENLABS_API_KEY not configured; skipping TTS")
        _client = None
        _last_api_key = None
        return None

    # Re-use or re-initialize client if API key changed
    if _client is None or api_key != _last_api_key:
        try:
            _client = ElevenLabs(api_key=api_key)
            _last_api_key = api_key
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to init ElevenLabs client: %s", exc)
            _client = None
            _last_api_key = None
            return None
    return _client


@lru_cache(maxsize=128)
def _synthesize_speech_memoized(text: str, voice_id: str, api_key: str) -> str:
    """Memoized helper function that calls the API.

    By accepting api_key, we ensure the cache is invalidated if the config
    changes. We raise exceptions inside the memoized function to avoid
    caching failure states.
    """
    client = _get_client()
    if not client:
        raise RuntimeError("ElevenLabs client not initialized")

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
        return None

    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    try:
        # Pass api_key to ensure cache isolation across config changes.
        return _synthesize_speech_memoized(text, voice_id, api_key)
    except Exception as exc:  # pylint: disable=broad-except
        # Return None so callers can still show text; log for visibility.
        logger.warning("ElevenLabs synthesis failed: %s", exc)
        return None


__all__ = ["synthesize_speech"]
