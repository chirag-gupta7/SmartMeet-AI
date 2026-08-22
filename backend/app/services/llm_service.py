import json
import logging
from functools import lru_cache
from typing import Tuple, Optional

from flask import current_app
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

HF_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"

# Updated Prompt for better intent recognition
SYSTEM_PROMPT = (
    "You are a smart voice assistant. "
    "Your goal is to classify user intent into JSON actions."
    " Respond ONLY in valid JSON format with keys: 'action' and 'reply'.\n\n"
    "RULES:\n"
    "1. If the user mentions 'meet', 'book', 'schedule', 'appointment', "
    "or 'calendar', classify as 'schedule_meeting'.\n"
    "2. If the user asks for weather, classify as 'weather'.\n"
    "3. Otherwise, use 'general_response'.\n"
    "4. 'reply' should be a short, friendly response spoken to the user.\n\n"
    "Valid 'action' values: ['schedule_meeting', 'weather', "
    "'general_response']"
)

# Cache for the HuggingFace InferenceClient instance
_hf_client: Optional[InferenceClient] = None


def _get_client(api_key: str) -> Optional[InferenceClient]:
    """Get or create a cached HuggingFace InferenceClient instance."""
    global _hf_client
    if _hf_client is not None:
        return _hf_client

    try:
        _hf_client = InferenceClient(token=api_key)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to init HuggingFace client: %s", exc)
        return None
    return _hf_client


@lru_cache(maxsize=100)
def _memoized_generate_action_reply(user_text: str, api_key: str) -> str:
    """
    Perform the actual LLM API call and cache results.
    Returns the cleaned raw string content from the LLM.
    Raises Exception on failure to avoid caching error states.
    """
    # BOLT OPTIMIZATION: reuse the cached client instead of creating a new
    # InferenceClient for every cache miss (allows HTTP connection reuse).
    client = _get_client(api_key)
    if not client:
        raise RuntimeError("HuggingFace client could not be initialized")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    response = client.chat_completion(
        model=HF_MODEL,
        messages=messages,
        max_tokens=150,
        temperature=0.3,
    )
    content = response.choices[0].message.content

    # Clean up potential markdown formatting (```json ... ```)
    if "```" in content:
        content = content.replace("```json", "").replace("```", "")

    return content.strip()


def generate_action_reply(user_text: str) -> Tuple[str, str]:
    api_key = current_app.config.get("HUGGINGFACE_API_KEY")
    if not api_key:
        logger.info("HUGGINGFACE_API_KEY not configured; skipping LLM call")
        return "general_response", "AI is not configured."

    try:
        # Use memoized helper to avoid redundant LLM calls for same transcript.
        # Exceptions are not cached by lru_cache, allowing retry on next call.
        content = _memoized_generate_action_reply(user_text, api_key)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Hugging Face generation failed: %s", exc)
        return "general_response", "I'm having trouble connecting to the brain."

    # Parse JSON
    action = "general_response"
    reply = "I understood, but couldn't generate a structured response."

    try:
        data = json.loads(content)
        if isinstance(data, dict):
            action = data.get("action") or action
            reply = data.get("reply") or reply
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from HF: %s", content)
        reply = content  # Fallback: just speak the raw text

    return action, reply


__all__ = ["generate_action_reply"]
