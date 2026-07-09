## 2025-05-15 - Caching External API Clients and Results
**Learning:** External API clients (ElevenLabs, HuggingFace) were being instantiated on every request, adding unnecessary overhead. Additionally, frequent voice commands like greetings were triggering redundant TTS API calls. Using `lru_cache` on functions that rely on `current_app.config` requires passing config values as arguments to ensure cache hits/misses are correct when configuration changes. Raising exceptions in memoized functions prevents caching of transient failure states.

**Action:** Implement a singleton pattern for API clients and use `lru_cache` for expensive synthesis/generation calls, ensuring all configuration dependencies are passed as parameters. Always clear caches in tests to ensure isolation.
