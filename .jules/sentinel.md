## 2026-03-30 - CPU DoS in Safe Arithmetic Evaluator
**Vulnerability:** Safe arithmetic evaluator (`ast.Pow`) allowed unbounded exponentiation (e.g. `2 ** 1000000`), causing excessive CPU/memory consumption (Denial of Service).
**Learning:** Restricting AST node types and using `ast.parse` prevents arbitrary code execution, but mathematical operators like exponentiation (`ast.Pow`) can still cause CPU resource exhaustion if operand magnitudes are not bounded.
**Prevention:** Bound exponent magnitudes (e.g. `abs(exponent) <= 1000`) before executing `ast.Pow` operations in custom expression evaluators.
