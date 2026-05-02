## 2025-05-02 - Theme Toggle Accessibility & Manual Overrides
**Learning:** Manual theme switching via `data-theme` must be explicitly mirrored in CSS and excluded from system-level dark mode media queries (using `:root:not([data-theme='light'])`) to ensure user preference is respected even if it differs from system settings.
**Action:** Always provide both media query and attribute-based selectors for theme variables, and use negative attribute selectors in media queries to avoid conflicts with manual overrides.
