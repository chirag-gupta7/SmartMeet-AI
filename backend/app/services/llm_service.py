import json
import logging
from typing import Tuple, Optional
from functools import lru_cache

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
def _get_client(api_key: str) -> Optional[InferenceClient]:
    """
    Memoize the InferenceClient instance to avoid redundant initializations.
    We pass api_key as an argument so the cache refreshes if the config
    changes.
    """
    if not api_key:
        logger.info("HUGGINGFACE_API_KEY not configured; skipping LLM call")
        return None
    return InferenceClient(token=api_key)


def generate_action_reply(user_text: str) -> Tuple[str, str]:
    """
    Generate an action and reply from user text.
    Wrapped by _generate_action_reply_cached for performance.
    """
    api_key = current_app.config.get("HUGGINGFACE_API_KEY")
    return _generate_action_reply_cached(user_text, api_key)


@lru_cache(maxsize=100)
def _generate_action_reply_cached(user_text: str,
                                  api_key: str) -> Tuple[str, str]:
    """
    Actual implementation of LLM call with memoization.
    api_key is passed to ensure cache invalidation if config changes.
    """
    client = _get_client(api_key)
    if not client:
        return "general_response", "AI is not configured."

    # Construct messages for Chat API
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    try:
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
        return ("general_response",
                "I'm having trouble connecting to the brain.")

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
        reply = content

    return action, reply
