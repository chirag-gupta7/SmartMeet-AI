import base64
import logging
from functools import lru_cache
from typing import Optional

from flask import current_app
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def _memoized_synthesize(
    text: str, api_key: str, voice_id: str
) -> Optional[str]:
    """Internal memoized function to perform TTS.

    Including api_key and voice_id in arguments ensures cache invalidation
    if configuration changes.
    """
    # We need a client here. Since we are inside lru_cache, we can't easily
    # use current_app, so we rely on the client being cached or re-initialized.
    # Actually, ElevenLabs client just needs the API key.
    try:
        client = ElevenLabs(api_key=api_key)
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
        )
        audio_bytes = b"".join(audio_stream)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        # We don't want to cache failure states ideally,
        # but lru_cache will cache the return value.
        # Raising an exception would avoid caching, but we'd need to catch it.
        logger.warning("ElevenLabs synthesis failed in memoized call: %s", exc)
        raise exc


def synthesize_speech(text: str) -> Optional[str]:
    """Convert text to base64-encoded audio using ElevenLabs."""
    if not text:
        return None

    api_key = current_app.config.get("ELEVENLABS_API_KEY")
    voice_id = current_app.config.get(
        "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
    )

    if not api_key:
        return None

    try:
        return _memoized_synthesize(text, api_key, voice_id)
    except Exception:
        # Fallback for when memoized call fails
        return None


__all__ = ["synthesize_speech"]
