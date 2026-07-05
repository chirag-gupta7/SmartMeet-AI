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
    "Valid 'action' values: "
    "['schedule_meeting', 'weather', 'general_response']"
)


@lru_cache(maxsize=1)
def _get_cached_client(api_key: Optional[str]) -> Optional[InferenceClient]:
    """
    Memoize the InferenceClient instance.
    Cached by api_key to ensure it updates if the config changes.
    """
    if not api_key:
        logger.info("HUGGINGFACE_API_KEY not configured; skipping LLM call")
        return None
    return InferenceClient(token=api_key)


@lru_cache(maxsize=128)
def _memoized_generate(api_key: Optional[str], user_text: str) -> str:
    """
    Core generation logic wrapped with lru_cache for result memoization.
    Takes api_key as argument to handle configuration changes correctly.
    Failure states are NOT cached as they raise an exception.
    """
    client = _get_cached_client(api_key)
    if not client:
        raise RuntimeError("AI is not configured.")

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

    # Extract the content from the response object
    content = response.choices[0].message.content

    # Clean up potential markdown formatting (```json ... ```)
    if "```" in content:
        content = content.replace("```json", "").replace("```", "")

    return content.strip()


def generate_action_reply(user_text: str) -> Tuple[str, str]:
    """
    Wrapper for generate_action_reply that handles caching and parsing.
    Optimized with result memoization and client instance caching.
    """
    api_key = current_app.config.get("HUGGINGFACE_API_KEY")

    try:
        content = _memoized_generate(api_key, user_text)
    except Exception as exc:
        logger.warning("Hugging Face generation failed: %s", exc)
        return "general_response", str(exc)

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
