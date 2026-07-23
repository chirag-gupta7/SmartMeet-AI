# ⚡ Bolt's Performance Journal

This journal documents critical performance learnings from our optimizations to avoid future regressions and make optimal design choices.

## 2026-07-23 - [Caching and Singleton API Clients]
**Learning:** Re-instantiating external API clients (like `ElevenLabs` or Hugging Face's `InferenceClient`) on every request adds significant connection overhead and CPU cycle wastage. Maintaining global singleton instances is highly efficient. Furthermore, caching response outputs (e.g., TTS base64 speech, LLM classification) with `functools.lru_cache` ensures sub-millisecond response times for frequent queries. To maintain correctness during configuration/API key changes, configuration parameters must be passed as arguments to the memoized helper function, and cache failures must not be cached (raise exceptions instead).
**Action:** Always wrap expensive external API calls with a singleton client retrieval and an `lru_cache` on a helper function, passing the API key as a parameter to ensure isolation and cache invalidation.

## 2026-07-23 - [Database Indexing for Filtered and Sorted Queries]
**Learning:** Querying a table like `meetings` with filters on `owner_id` and sorting on `start_time` triggers expensive full-table scans in SQLite/PostgreSQL as the table grows. Adding explicit indices on filtering (`owner_id`) and sorting (`start_time`) columns speeds up lookup and sort planning to logarithmic time complexity.
**Action:** Define explicit `index=True` on columns involved in frequent filters (`WHERE` clauses) or sorting (`ORDER BY` clauses) in the SQLAlchemy model definitions.
