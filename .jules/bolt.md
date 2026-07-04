## 2026-07-04 - [ElevenLabs TTS Caching & Memoization]
**Learning:** Initializing the ElevenLabs client on every request adds significant overhead (~34ms in benchmarks), and repeated TTS requests for the same text incur high API latency and costs. Using `lru_cache` for both the client instance and the synthesis results significantly improves efficiency.
**Action:** Always cache expensive third-party client instances and memoize idempotent API calls (like TTS) while ensuring exception-throwing paths are not cached.
