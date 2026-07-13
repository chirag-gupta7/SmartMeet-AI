## 2025-12-10 - LLM and TTS Service Optimization
**Learning:** External API clients (Hugging Face InferenceClient, ElevenLabs) were being re-instantiated on every request, and redundant API calls were being made for frequent identical queries (like the initial greeting).
**Action:** Implemented a singleton client pattern that only re-initializes when the API key changes. Added `lru_cache` memoization to service calls, using a wrapper that includes configuration parameters (API key, voice ID) in the cache key to ensure cache validity during configuration changes.

## 2025-12-10 - Cache Validity with Dynamic Config
**Learning:** When using `functools.lru_cache` in a Flask app where configuration can change (e.g., via environment variables or settings), caching functions that implicitly rely on `current_app.config` can lead to stale results if the config changes but the function arguments remain the same.
**Action:** Pass critical configuration values (like API keys) as arguments to the memoized function. This ensures the cache naturally partitions by configuration state.
