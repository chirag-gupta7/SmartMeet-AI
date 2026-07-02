## 2025-05-15 - Optimizing External API latency with Client Caching and Memoization

**Learning:** Initializing external API clients (ElevenLabs, Hugging Face) on every request introduces unnecessary overhead. Furthermore, many voice assistant interactions (like greetings or common intent classifications) are repetitive, leading to redundant network latency and API costs.

**Action:** Implement a pattern of client instance caching (using a global dict keyed by API key) and result memoization (using `functools.lru_cache`). Ensure the memoized function is a thin wrapper that raises exceptions so failures aren't cached, and include configuration values (like `api_key` or `voice_id`) in the cache key to handle config changes correctly.
