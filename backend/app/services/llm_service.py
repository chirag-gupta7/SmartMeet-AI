import json
import logging
from functools import lru_cache
from typing import Tuple, Optional

from flask import current_app
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

HF_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"

# Global client cache
_hf_client: Optional[InferenceClient] = None

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
    "Valid 'action' values: "
    "['schedule_meeting', 'weather', 'general_response']"
)


def _get_client():
    global _hf_client
    api_key = current_app.config.get("HUGGINGFACE_API_KEY")
    if not api_key:
        logger.info("HUGGINGFACE_API_KEY not configured; skipping LLM call")
        return None

    if _hf_client is None:
        # Cache the client instance to avoid repeated initialization
        _hf_client = InferenceClient(token=api_key)
    return _hf_client


@lru_cache(maxsize=128)
def _cached_generate_action_reply(
    user_text: str, api_key: str
) -> Tuple[str, str]:
    """Internal helper to memoize LLM responses based on text and API key."""
    client = _get_client()
    if not client:
        return "general_response", "AI is not configured."

    # Construct messages for Chat API
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    try:
        # Optimized: reduced max_tokens if only action/reply are needed
        response = client.chat_completion(
            model=HF_MODEL,
            messages=messages,
            max_tokens=150,
            temperature=0.3,
        )

        # Extract the content from the response object
        content = response.choices[0].message.content

        # Clean up potential markdown formatting (```json ... ```)
        if "```" in content:
            content = content.replace("```json", "").replace("```", "")

        content = content.strip()

    except Exception as exc:
        logger.warning("Hugging Face generation failed: %s", exc)
        # We don't want to cache failure states ideally, but for now we return
        # a fallback. In a more robust system, we might raise an exception
        # so lru_cache doesn't store it.
        return (
            "general_response",
            "I'm having trouble connecting to the brain."
        )

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


def generate_action_reply(user_text: str) -> Tuple[str, str]:
    """
    Classify user intent and generate a reply.
    Uses lru_cache via a helper to avoid redundant API calls.
    """
    api_key = current_app.config.get("HUGGINGFACE_API_KEY")
    if not api_key:
        return "general_response", "AI is not configured."

    # Pass api_key to the cached function so if it changes, cache is
    # invalidated
    return _cached_generate_action_reply(user_text, api_key)
