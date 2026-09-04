## 2026-08-30 - ARIA Status Announcements and Error Tone Feedback for Async Actions
**Learning:** Dynamic status and error messages updated asynchronously (such as calendar sync or voice error banners) are invisible to screen readers unless marked with `role="status"` or `role="alert"` and `aria-live="polite"`. Furthermore, failure states rendered in positive colors (e.g. green) violate expected visual error affordances.
**Action:** Always include `role="status"` or `role="alert"` on dynamic feedback containers, and conditionally apply error text styling (e.g. `text-red-600` vs `text-emerald-600`) based on success/failure state.

## 2025-05-15 - Explicit Modifiers for Global Keyboard Shortcuts
**Learning:** Global keyboard listeners attached to single keys like `Space` hijack native browser functionality (such as page scrolling and focus activation on buttons/inputs).
**Action:** Always use modifier key combinations (e.g. `Ctrl + Space` / `Cmd + Space`) for global component shortcuts to ensure keyboard accessibility and native browser interactions are preserved.
