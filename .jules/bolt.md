## 2025-05-15 - Optimizing AI service calls with memoization
**Learning:** External AI services (LLM and TTS) are significant performance bottlenecks. Result memoization with `lru_cache` and client instance caching can drastically reduce latency for repeated requests and avoid redundant initialization overhead.
**Action:** Always consider caching strategy for external API calls, especially when inputs are likely to repeat. Ensure cache invalidation by including configuration parameters (like API keys or model IDs) in the cache key.
