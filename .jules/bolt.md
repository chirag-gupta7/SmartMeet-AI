# Bolt's Performance Journal

## 2025-05-14 - Optimized External API Services
**Learning:** External API clients (ElevenLabs, HuggingFace) were being re-instantiated on every request, and identical text was being re-processed, causing unnecessary latency and overhead. Using `lru_cache` on a helper function that takes configuration (API keys) as arguments allows for safe memoization that respects configuration changes.
**Action:** Always consider memoizing external API calls and client initializations, especially for expensive operations like LLM generation and TTS. Ensure cache keys include configuration values to avoid stale caches.

## 2025-05-15 - TTS Memoization & Client Caching
**Learning:** ElevenLabs TTS service was initializing a new client on every request and making redundant API calls for identical text. Implementing `lru_cache` for results and caching the client instance drastically reduces latency (up to 50x in benchmarks) and saves on API costs.
**Action:** Always check for repeated API calls and expensive client initializations in voice/TTS services and apply memoization patterns where appropriate.

## 2025-05-15 - Optimizing AI Service Latency with Memoization
**Learning:** External API calls for Text-to-Speech (ElevenLabs) and LLM intent recognition (HuggingFace) are significant latency bottlenecks. Repeated requests for identical content (e.g., greetings, common commands) can be eliminated using memoization.
**Action:** Implement `functools.lru_cache` for API results. Ensure that configuration values like API keys or Voice IDs are included in the cache key to prevent stale data if settings change. Use client instance caching to avoid redundant SDK initialization overhead.

## 2025-05-15 - Memoization of AI Service Clients and Results
**Learning:** Initializing external API clients (Hugging Face, ElevenLabs) on every request and re-fetching identical results (like greetings or common intents) adds significant latency and overhead.
**Action:** Use `functools.lru_cache` to memoize client instances based on API keys and cache result mappings. Ensure failure states are not cached by raising exceptions in the memoized functions and catching them in public wrappers.

## 2025-05-15 - [Memoization for LLM and TTS Services]
**Learning:** Caching service client instances (like HuggingFace InferenceClient and ElevenLabs) using `lru_cache(maxsize=1)` significantly reduces initialization overhead and allows for HTTP connection reuse. Caching API results for identical queries further eliminates network latency and cost for repeated user interactions.
**Action:** Always implement memoization for idempotent external API calls, ensuring cache keys include relevant configuration (API keys, model IDs) to handle dynamic configuration changes safely.

## 2025-05-15 - Caching External API Responses
**Learning:** Implementing `lru_cache` for external API services (LLM, TTS) significantly reduces latency for repeated user inputs. It's critical to separate the API call from error handling so that failures are not cached. Additionally, passing configuration values like API keys as arguments to cached functions ensures the cache remains valid after configuration changes.
**Action:** Always use a wrapper pattern for caching API calls: a decorated internal function for the actual call (raising exceptions) and a public function that handles exceptions and provides fallbacks.

## 2025-05-15 - LLM/TTS Cache Wrapper Pattern
**Learning:** Implementing `lru_cache` for external API services (LLM, TTS) significantly reduces latency for repeated user inputs. It's critical to separate the API call from error handling so that failures are not cached. Additionally, passing configuration values like API keys as arguments to cached functions ensures the cache remains valid after configuration changes.
**Action:** Always use a wrapper pattern for caching API calls: a decorated internal function for the actual call (raising exceptions) and a public function that handles exceptions and provides fallbacks.

## 2025-05-15 - Optimizing AI service calls with memoization
**Learning:** External AI services (LLM and TTS) are significant performance bottlenecks. Result memoization with `lru_cache` and client instance caching can drastically reduce latency for repeated requests and avoid redundant initialization overhead.
**Action:** Always consider caching strategy for external API calls, especially when inputs are likely to repeat. Ensure cache invalidation by including configuration parameters (like API keys or model IDs) in the cache key.

## 2025-05-22 - TTS Service Optimization
**Learning:** External API calls for voice synthesis (TTS) are a major source of latency (often >1s) and cost. Frequent UI phrases like greetings are identical across sessions and should be cached.
**Action:** Use `functools.lru_cache` for synthesis results and cache the client instance. Avoid caching `None` or failure states by raising exceptions within the memoized function, ensuring retries on subsequent calls.

## 2025-05-22 - [AI Service Optimization]
**Learning:** External AI services (LLM and TTS) were being re-instantiated and called on every request, even for identical inputs, leading to unnecessary latency and potential cost. Using `lru_cache` significantly reduces latency for repeated phrases (like greetings or common commands).
**Action:** Always implement client instance caching and result memoization for external AI APIs. Ensure that failure states are NOT cached by raising exceptions in the memoized function and catching them in a wrapper. Pass configuration values as arguments to the memoized function to handle dynamic configuration changes correctly.
## 2026-06-29 - [Memoized External API Calls]
**Learning:** External API calls like ElevenLabs TTS and Hugging Face LLM are major bottlenecks due to network latency. Using `lru_cache` significantly improves responsiveness for repeated identical inputs.
**Action:** Always consider memoization for idempotent external API calls, ensuring cache keys include configuration values to handle changes correctly.
