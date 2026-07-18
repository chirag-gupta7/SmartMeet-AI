## 2025-02-18 - Client Singletons and Memoization with Config Updates
**Learning:** Instantiating external API clients (like ElevenLabs and InferenceClient) on every request introduces unnecessary latency and memory overhead. Using a global singleton pattern keeps the same client instance alive. Furthermore, memoizing external API calls with `lru_cache` on a helper function that takes the API key/config as an argument prevents caching stale results when the application configuration changes. It also ensures that failures are not cached by raising exceptions in the memoized helper.
**Action:** Always wrap memoized API calls in a wrapper that catches exceptions, use cached helper functions that accept key configurations, and reuse client singletons when possible.

## 2025-02-18 - Database Indexing on Queried and Sorted Fields
**Learning:** Queries that filter on foreign keys and sort by timestamp (such as fetching a user's meetings sorted by start time) suffer from linear scans (O(n)) as the dataset grows. Adding explicit indices to both `owner_id` and `start_time` reduces lookup and sorting complexity to O(log n).
**Action:** Identify and apply indexes on foreign key columns and sorted datetime columns in SQLAlchemy models to optimize list operations.
