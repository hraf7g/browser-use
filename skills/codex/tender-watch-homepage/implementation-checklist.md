# Implementation Checklist

Use this as the ship checklist for any Tender Watch homepage rewrite or major homepage refresh.

## Narrative

- Hero clearly identifies Tender Watch as an AI-powered tender monitoring platform.
- Copy is MENA-oriented, not UAE-only.
- The page explicitly explains browse -> extract -> analyze -> match -> alert.
- Browser automation is visible and described as the collection mechanism.
- Arabic and English tender handling is visible and described.
- Matching is described as company-profile based, not generic keyword spam.

## Content Integrity

- No fake numbers.
- No fake source counts.
- No fake customer logos.
- No fake testimonials.
- No fake integrations.
- No dead CTAs.
- No unsupported market-leader language.

## UX and Design

- Header remains compatible with current navigation and auth routes.
- Layout works in both English and Arabic.
- Layout remains coherent in RTL.
- Visual hierarchy feels premium and calm, not noisy.
- Homepage sections are not repetitive or filler-heavy.
- The page teaches the product visually, not only through text.

## Motion

- Hero animation exists or a static equivalent clearly conveys the workflow.
- Motion is transform/opacity-first where possible.
- Motion does not harm readability.
- `prefers-reduced-motion` has a clear fallback.
- The reduced-motion version still explains the product.

## Code Quality

- Follows existing frontend architecture.
- Uses TypeScript throughout.
- Uses existing translation system instead of hardcoded mixed-language UI.
- New components are split by section, not dumped into one large page file.
- Shared helpers live in `frontend/src/lib/` when reused.
- No unnecessary client boundaries.

## Verification

- Review English homepage route.
- Review Arabic homepage route or language toggle state.
- Verify hero, key sections, and CTAs in both LTR and RTL.
- Verify light and dark themes if homepage supports both.
- Verify reduced motion behavior.

Run:

- `npm run typecheck`
- `npm run build`

If changes are larger than a small copy pass, also verify:

- there are no hydration issues
- section anchors still work
- auth CTAs still resolve to live routes

## Completion Standard

Do not close the task until:

- the homepage tells a clear operational story
- the hero demonstrates the product logic
- the page feels premium and trustworthy
- the implementation passes typecheck and build
