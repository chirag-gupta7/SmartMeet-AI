## 2026-07-11 - ElevenLabs Service Optimization
**Learning:** Instantiating the ElevenLabs client on every request is expensive and unnecessary. Caching TTS results can significantly reduce API costs and latency for repeated phrases (like greetings).
**Action:** Implement singleton pattern for API clients and use `lru_cache` for idempotent API calls, ensuring cache keys include configuration values to handle changes.
