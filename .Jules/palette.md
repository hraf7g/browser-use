## 2025-05-15 - [Accessible & Animated Theme Toggle]
**Learning:** Manual theme overrides should use specific selectors like `[data-theme='dark']` alongside `@media (prefers-color-scheme: dark)` to ensure the user's preference is respected over the system setting. Adding smooth transitions to `body` and `content-card` significantly improves the perceived quality of theme switching.
**Action:** Always mirror system dark mode variables in a `[data-theme='dark']` selector and apply global transitions to background and text colors.
