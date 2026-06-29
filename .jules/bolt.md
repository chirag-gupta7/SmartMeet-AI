# Bolt's Performance Journal
## 2026-06-29 - [Memoized External API Calls]
**Learning:** External API calls like ElevenLabs TTS and Hugging Face LLM are major bottlenecks due to network latency. Using `lru_cache` significantly improves responsiveness for repeated identical inputs.
**Action:** Always consider memoization for idempotent external API calls, ensuring cache keys include configuration values to handle changes correctly.
