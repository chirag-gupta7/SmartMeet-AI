## 2026-03-30 - CPU DoS in Safe Arithmetic Evaluator
**Vulnerability:** Safe arithmetic evaluator (`ast.Pow`) allowed unbounded exponentiation (e.g. `2 ** 1000000`), causing excessive CPU/memory consumption (Denial of Service).
**Learning:** Restricting AST node types and using `ast.parse` prevents arbitrary code execution, but mathematical operators like exponentiation (`ast.Pow`) can still cause CPU resource exhaustion if operand magnitudes are not bounded.
**Prevention:** Bound exponent magnitudes (e.g. `abs(exponent) <= 1000`) before executing `ast.Pow` operations in custom expression evaluators.

## 2026-03-30 - Unbounded String Input in Fallback ISO Datetime Parser
**Vulnerability:** `parse_iso_datetime` accepted arbitrarily long strings without length bounds, falling back to `dateutil.parser.parse` which executed CPU-intensive fuzzy parsing loops on invalid non-ISO strings, causing CPU resource exhaustion.
**Learning:** Functions that wrap third-party parsing tools (such as `dateutil.parser.parse`) should validate input string lengths beforehand, as non-matching oversized strings can trigger catastrophic algorithmic complexity or high CPU usage.
**Prevention:** Always bound input string lengths (e.g. `len(value_str) <= 128` for ISO datetimes) before passing string inputs to generic or fuzzy parser libraries.
