# Bolt's Performance Journal ⚡

## 2025-05-15 - LLM and TTS Service Optimization
**Learning:** External API clients (Hugging Face InferenceClient, ElevenLabs) were being re-instantiated on every request, and identical queries were triggering redundant network calls. Implementing a singleton pattern for clients and using `lru_cache` for response memoization significantly reduces latency and resource usage.
**Action:** Always check for redundant object instantiation and network calls in service layers. Use memoized helpers that include configuration keys (like API keys) in their arguments to ensure cache validity during configuration changes. Ensure singleton clients are integrated within these memoized helpers for maximum efficiency.
