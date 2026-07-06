## 2025-05-22 - [Optimizing External AI Service Integrations]
**Learning:** External API services (LLM and TTS) in this codebase were re-instantiating clients and re-executing identical network calls on every request. Client instantiation for libraries like `elevenlabs` and `huggingface_hub` can be expensive.
**Action:** Implement global client instance caching and result memoization using `lru_cache`. Ensure that configuration-dependent values (like API keys) are passed as arguments to the cached function to handle runtime configuration changes correctly.

## 2025-05-22 - [`lru_cache` Keyword Argument Surprise]
**Learning:** `functools.lru_cache` in Python uses `maxsize` as the keyword argument, not `max_size`.
**Action:** Always use `maxsize` when configuring `lru_cache` to avoid `TypeError`.
