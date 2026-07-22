# Bolt's Performance Journal

## 2026-07-22 - [Optimizing External APIs & Database Queries]
**Learning:** External API services (like Hugging Face LLM and ElevenLabs TTS) have non-trivial request costs and response latencies. Initializing API client instances repeatedly introduces overhead. Additionally, Flask app configuration changes require caches to isolate configuration values like API keys so that different credentials do not result in cache-leakage. Finally, SQLite foreign key relationships (such as owner_id on meetings) are not indexed automatically, leading to slow sequential scans on meeting listings.
**Action:**
1. Use lazy-initialized, singleton client instances that re-instantiate only when the API key changes.
2. Utilize `functools.lru_cache` on helper functions where configuration arguments (e.g., API keys, voice IDs) are passed explicitly, maintaining cache separation and context independence.
3. Avoid caching transient errors by raising exceptions from the memoized helpers and catching them inside wrappers.
4. Add explicit database indices on foreign keys and frequently queried or sorted fields, verifying index creation and query plans via tests.
