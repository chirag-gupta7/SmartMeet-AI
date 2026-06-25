## 2025-05-15 - [Memoization for LLM and TTS Services]
**Learning:** Caching service client instances (like HuggingFace InferenceClient and ElevenLabs) using `lru_cache(maxsize=1)` significantly reduces initialization overhead and allows for HTTP connection reuse. Caching API results for identical queries further eliminates network latency and cost for repeated user interactions.
**Action:** Always implement memoization for idempotent external API calls, ensuring cache keys include relevant configuration (API keys, model IDs) to handle dynamic configuration changes safely.
