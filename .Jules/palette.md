## 2025-05-14 - Dark Mode Persistence and Accessibility Standards
**Learning:** Manual theme toggling using `data-theme` requires explicit mirroring of `@media (prefers-color-scheme: dark)` variables in a CSS attribute selector to avoid conflicts with system settings. Accessibility for icon-only buttons requires both `aria-label` for screen readers and `title` for visual tooltips.
**Action:** Always mirror dark mode variables in `[data-theme='dark']` and ensure icon-only buttons have both `aria-label` and `title`.
