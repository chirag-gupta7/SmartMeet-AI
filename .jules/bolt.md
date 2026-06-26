## 2025-05-15 - Caching External API Responses

**Learning:** Implementing `lru_cache` for external API services (LLM, TTS) significantly reduces latency for repeated user inputs. It's critical to separate the API call from error handling so that failures are not cached. Additionally, passing configuration values like API keys as arguments to cached functions ensures the cache remains valid after configuration changes.

**Action:** Always use a wrapper pattern for caching API calls: a decorated internal function for the actual call (raising exceptions) and a public function that handles exceptions and provides fallbacks.
