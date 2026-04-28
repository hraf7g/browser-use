## 2025-05-22 - Theme Switcher Reliability and Polish
**Learning:** Manual theme overrides (using a `data-theme` attribute) must be explicitly mirrored in CSS and the `prefers-color-scheme` media query should be scoped with `:root:not([data-theme='light'])` to avoid conflicts. Transitioning from emojis to library icons (`lucide-react`) significantly improves the professional feel of micro-interactions.
**Action:** Always verify theme variable mirroring in `globals.css` when implementing theme toggles, and prioritize standard icon libraries over emojis for core UI controls.
