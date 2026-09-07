## 2026-08-30 - ARIA Status Announcements and Error Tone Feedback for Async Actions
**Learning:** Dynamic status and error messages updated asynchronously (such as calendar sync or voice error banners) are invisible to screen readers unless marked with `role="status"` or `role="alert"` and `aria-live="polite"`. Furthermore, failure states rendered in positive colors (e.g. green) violate expected visual error affordances.
**Action:** Always include `role="status"` or `role="alert"` on dynamic feedback containers, and conditionally apply error text styling (e.g. `text-red-600` vs `text-emerald-600`) based on success/failure state.

## 2025-05-15 - Explicit Modifiers for Global Keyboard Shortcuts
**Learning:** Global keyboard listeners attached to single keys like `Space` hijack native browser functionality (such as page scrolling and focus activation on buttons/inputs).
**Action:** Always use modifier key combinations (e.g. `Ctrl + Space` / `Cmd + Space`) for global component shortcuts to ensure keyboard accessibility and native browser interactions are preserved.

## 2026-09-01 - Error Recovery and Live Feedback in Asynchronous UI
**Learning:** Transient Web API errors (like Web Speech API timeouts or recognition errors) permanently disable key controls if error state isn't resetable, trapping users. Combining `role="alert"` for screen reader announcements with an explicit "Try again" action button restores user agency without page reloads.
**Action:** Provide explicit inline retry actions inside error banners with `role="alert"` for transient UI/speech errors, and keep interactive controls enabled for retry attempts when supported.
