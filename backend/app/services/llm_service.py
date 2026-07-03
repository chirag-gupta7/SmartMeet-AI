import functools
import json
import logging
from typing import Tuple, Dict, Optional

from flask import current_app
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

HF_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"

# Global client cache to avoid recreating InferenceClient on every request
_hf_clients_cache: Dict[str, InferenceClient] = {}

# Updated Prompt for better intent recognition
SYSTEM_PROMPT = (
    "You are a smart voice assistant. "
    "Your goal is to classify user intent into JSON actions."
    " Respond ONLY in valid JSON format with keys: 'action' and 'reply'.\n\n"
    "RULES:\n"
    "1. If the user mentions 'meet', 'book', 'schedule', "
    "'appointment', or 'calendar', classify as 'schedule_meeting'.\n"
    "2. If the user asks for weather, classify as 'weather'.\n"
    "3. Otherwise, use 'general_response'.\n"
    "4. 'reply' should be a short, friendly response spoken to the user.\n\n"
    "Valid 'action' values: "
    "['schedule_meeting', 'weather', 'general_response']"
)


def _get_client(api_key: str) -> Optional[InferenceClient]:
    """Retrieves or creates a cached InferenceClient for the given API key."""
    if api_key not in _hf_clients_cache:
        _hf_clients_cache[api_key] = InferenceClient(token=api_key)
    return _hf_clients_cache[api_key]


@functools.lru_cache(maxsize=128)
def _memoized_generate_action_reply(
    user_text: str, api_key: str
) -> Tuple[str, str]:
    """Internal memoized LLM call to reduce redundant API requests."""
    client = _get_client(api_key)

    # Construct messages for Chat API
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    # Note: Exceptions are NOT caught here to avoid caching failure states
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
    Classifies user intent and generates a reply.
    Optimized with client caching and result memoization.
    """
    api_key = current_app.config.get("HUGGINGFACE_API_KEY")
    if not api_key:
        logger.info("HUGGINGFACE_API_KEY not configured; skipping LLM call")
        return "general_response", "AI is not configured."

    try:
        # Wrap the memoized call to handle transient API failures
        # without caching them
        return _memoized_generate_action_reply(user_text, api_key)
    except Exception as exc:
        logger.warning("Hugging Face generation failed: %s", exc)
        return (
            "general_response",
            "I'm having trouble connecting to the brain.",
        )
