## 2026-04-29 - Theme Mirroring for Manual Toggles
**Learning:** When using a manual theme toggle that sets a `data-theme` attribute, CSS variables defined in `@media (prefers-color-scheme: dark)` must be mirrored in a `[data-theme='dark']` selector and media queries should use `:root:not([data-theme='light'])` to ensure the manual override correctly respects user preference across all states.
**Action:** Always mirror dark theme variables in a data-attribute selector when implementing manual theme switching logic.
