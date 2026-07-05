## 2025-05-15 - LLM Service Optimization
**Learning:** External API calls for intent classification are often redundant and have high latency. Using `lru_cache` for both the client instance and the results can reduce latency from seconds to milliseconds for repeated queries.
**Action:** Always implement client caching and result memoization for intent classifiers with low temperature. Ensure failure states are not memoized.
