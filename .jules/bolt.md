## 2025-05-15 - Memoization of AI Service Clients and Results
**Learning:** Initializing external API clients (Hugging Face, ElevenLabs) on every request and re-fetching identical results (like greetings or common intents) adds significant latency and overhead.
**Action:** Use `functools.lru_cache` to memoize client instances based on API keys and cache result mappings. Ensure failure states are not cached by raising exceptions in the memoized functions and catching them in public wrappers.
