## 2025-05-15 - TTS Memoization & Client Caching
**Learning:** ElevenLabs TTS service was initializing a new client on every request and making redundant API calls for identical text. Implementing `lru_cache` for results and caching the client instance drastically reduces latency (up to 50x in benchmarks) and saves on API costs.
**Action:** Always check for repeated API calls and expensive client initializations in voice/TTS services and apply memoization patterns where appropriate.
