## 2025-05-15 - [Memoization with Configuration Sensitivity]
**Learning:** When using `lru_cache` in a Flask application where the cached value depends on `current_app.config` (e.g., API keys), the configuration values must be passed as arguments to the memoized function. This ensures that the cache correctly handles changes to the configuration and avoids sharing state between different application instances or environments if they share the same process.
**Action:** Always pass relevant configuration strings (like API keys or voice IDs) as arguments to functions decorated with `lru_cache`.

## 2025-05-15 - [Avoiding Error Caching in LLM/TTS]
**Learning:** Caching failure states (exceptions) from external APIs can lead to persistent errors even after the external service recovers.
**Action:** Raise exceptions in the memoized function and catch them in a wrapper to ensure only successful responses are cached.
