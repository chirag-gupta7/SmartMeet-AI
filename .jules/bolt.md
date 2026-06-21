## 2025-05-22 - TTS Service Optimization
**Learning:** External API calls for voice synthesis (TTS) are a major source of latency (often >1s) and cost. Frequent UI phrases like greetings are identical across sessions and should be cached.
**Action:** Use `functools.lru_cache` for synthesis results and cache the client instance. Avoid caching `None` or failure states by raising exceptions within the memoized function, ensuring retries on subsequent calls.
