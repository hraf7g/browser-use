---
name: tender-watch-homepage
description: Build or replace the Tender Watch homepage in Next.js, TypeScript, and Tailwind when the goal is a premium MENA AI tender-monitoring homepage that explains browser automation across official procurement sites, Arabic/English analysis, company-profile matching, and alerts without fake claims, fake numbers, dead CTAs, or generic startup-page patterns.
---

# Tender Watch Homepage

Use this skill when working on the public Tender Watch homepage or homepage-like hero sections.

This skill is for a production homepage, not a generic SaaS landing page. The page must position Tender Watch as an AI platform that:

- browses official tender and procurement sites
- detects newly published contracts
- reads Arabic and English tender content
- extracts structured opportunity data
- matches tenders against a company profile
- sends instant alerts and daily briefs

## Non-negotiables

- Stack: Next.js + TypeScript + Tailwind.
- Respect the existing frontend architecture, route structure, translation system, theme handling, and local component patterns.
- Keep real CTAs only. Use existing routes such as `/signup`, `/login`, or real in-product pages.
- Do not invent counts, customers, logos, coverage maps, source totals, savings percentages, or “trusted by” claims.
- Position for MENA, not UAE-only.
- Be English + Arabic ready from the start. Layout must remain coherent under RTL.
- Tone is premium, calm, operational, and trustworthy.
- Do not use military, surveillance, “intel”, “command center”, or “war room” phrasing.
- Do not imply fake autonomous thought, human-like judgment, or mystical AI behavior.

## Core Homepage Job

The homepage should make this operating model visually obvious:

1. Browse official procurement sites
2. Extract contract details
3. Analyze Arabic and English tender content
4. Match against company profile and scope
5. Send alerts and daily briefs

If the page does not explain that flow clearly, it is not done.

## Architecture Rules

- Prefer replacing or upgrading the existing homepage sections instead of introducing a disconnected mini-app.
- Reuse existing translation/context/theme primitives.
- Keep component ownership clear. Favor a homepage section component per major block.
- Put reusable homepage-only formatting helpers in `frontend/src/lib/` if multiple sections need them.
- Keep props typed and narrow.
- Do not add client components unless motion, interactivity, or browser APIs require them.
- If animation is needed, keep the data model serializable and deterministic.

## Required Narrative

The page should answer these questions in order:

1. What is Tender Watch?
   A MENA tender monitoring platform powered by AI and browser automation.
2. What does it actually do?
   It visits official sources, reads tenders, extracts structured signals, and alerts teams when something relevant appears.
3. Why is it useful?
   It reduces manual portal checking and surfaces opportunities that fit the company profile.
4. Why trust it?
   Official-source positioning, operational clarity, bilingual analysis, and explicit explanation of what gets matched and why.
5. What should the visitor do next?
   Start monitoring or sign in.

## Preferred Section Stack

Use the smallest set of sections that can carry the story cleanly:

1. Header
2. Hero with product animation
3. Operating flow section: browse -> extract -> analyze -> match -> alert
4. Product proof section showing real product surfaces or realistic UI states
5. Company-fit section explaining profile-based matching, country scope, and industry scope
6. Delivery section for instant alerts and daily briefs
7. FAQ
8. Final CTA

Avoid filler sections like logo clouds, vanity metrics, vague testimonials, or repeated feature cards.

## Hero Requirements

The hero is the most important area on the page.

It must communicate:

- official-source monitoring across MENA
- browser automation as the collection mechanism
- Arabic/English content handling
- profile-based matching
- immediate operational outcomes

### Required hero animation concept

Design a restrained product animation where:

1. An AI cursor or arrow moves across official procurement source cards
2. One card opens into a tender page view
3. A scan pass highlights Arabic and English content blocks
4. Structured contract chips/cards are extracted from the page
5. A company profile panel evaluates the opportunity
6. A matched state is created
7. An alert card or daily brief card is emitted

This should feel like operational software, not a sci-fi demo.

Read [motion-system.md](motion-system.md) before implementing the hero animation.

## Copy Rules

Read [copy-system.md](copy-system.md) before writing or revising homepage copy.

Short version:

- Favor concrete product language over slogans.
- Name real actions: browse, extract, analyze, match, alert.
- Use “official sources”, “procurement portals”, “tender pages”, “company profile”, “daily brief”.
- Avoid empty claims like “revolutionary”, “magical”, “game-changing”, “10x”, “best-in-class”.
- Avoid fake specificity.

## Visual Direction

- Premium and quiet over loud and noisy.
- Strong information hierarchy.
- Use depth, panels, layered frames, and subtle motion rather than decorative clutter.
- Show product logic visually. The page should teach the workflow.
- Preserve the project’s existing visual language where it already works; elevate it rather than rebranding everything blindly.

## Accessibility and Motion

- All essential content must remain understandable with motion disabled.
- Respect `prefers-reduced-motion`.
- Keep animation durations modest.
- Avoid constant looping motion that distracts from reading.
- Ensure Arabic line-height and section density remain comfortable.

Read [motion-system.md](motion-system.md) before implementing any non-trivial movement.

## Verification Standard

Use [implementation-checklist.md](implementation-checklist.md) as the ship checklist.

Minimum verification after homepage changes:

- `npm run typecheck`
- `npm run build`

If changes affect translations, verify both English and Arabic states manually in code review.
If motion is added, verify the reduced-motion branch exists and leaves the page coherent.

## Working Method

1. Inspect the current homepage route and section components first.
2. Keep the existing architecture unless there is a clear structural reason to refactor.
3. Define the new narrative before writing UI code.
4. Implement the hero and operating flow first.
5. Add supporting sections only if they serve the core story.
6. Run the full verification checklist before closing.

## Deliverable Standard

A successful homepage should make a technical buyer or operator think:

- this monitors official tender sites across MENA
- this clearly handles Arabic and English content
- this matches tenders against my business scope
- this feels operational and trustworthy
- this is a real product, not a vague AI promise
