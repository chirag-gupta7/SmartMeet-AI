# Bolt's Performance Journal

## 2025-05-15 - Optimizing AI Service Latency with Memoization
**Learning:** External API calls for Text-to-Speech (ElevenLabs) and LLM intent recognition (HuggingFace) are significant latency bottlenecks. Repeated requests for identical content (e.g., greetings, common commands) can be eliminated using memoization.

**Action:** Implement `functools.lru_cache` for API results. Ensure that configuration values like API keys or Voice IDs are included in the cache key to prevent stale data if settings change. Use client instance caching to avoid redundant SDK initialization overhead.
