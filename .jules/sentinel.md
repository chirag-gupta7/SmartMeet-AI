## 2026-03-30 - API Key Exposure in Third-Party Request Exceptions
**Vulnerability:** External HTTP requests passing credentials via URL query parameters (e.g. `appid=api_key`) can leak sensitive keys in `RequestException` messages (`str(e)`), exposing keys in application logs, database log entries, and API error responses.
**Learning:** Python `requests.exceptions.RequestException` default string formatting includes the full requested URL, which exposes raw query parameters if credentials are included in the query string rather than HTTP headers or if exception messages are logged/returned directly.
**Prevention:** Redact API key strings from exception detail messages before logging or embedding exception text into return data structures.

## 2026-03-30 - CPU DoS in Safe Arithmetic Evaluator
**Vulnerability:** Safe arithmetic evaluator (`ast.Pow`) allowed unbounded exponentiation (e.g. `2 ** 1000000`), causing excessive CPU/memory consumption (Denial of Service).
**Learning:** Restricting AST node types and using `ast.parse` prevents arbitrary code execution, but mathematical operators like exponentiation (`ast.Pow`) can still cause CPU resource exhaustion if operand magnitudes are not bounded.
**Prevention:** Bound exponent magnitudes (e.g. `abs(exponent) <= 1000`) before executing `ast.Pow` operations in custom expression evaluators.
