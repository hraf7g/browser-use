# Motion System

Use this when implementing homepage motion for Tender Watch.

## Motion Principles

- Motion explains the product workflow.
- Motion is secondary to comprehension.
- Motion should feel precise, calm, and infrastructural.
- Prefer one strong sequence over many unrelated micro-animations.

## Performance Rules

- Prefer transform and opacity animation.
- Avoid layout-thrashing animations.
- Avoid heavy blur changes, oversized shadows, and continuous SVG filter effects.
- Keep simultaneous moving elements limited.
- Any loop should pause naturally and avoid attracting constant attention.

## Accessibility Rules

- Use `prefers-reduced-motion` to disable or drastically simplify motion.
- Reduced motion should still show state changes through static layering, highlighting, or step indicators.
- Do not gate understanding behind animation timing.

## Hero Animation Blueprint

Build the hero as a staged product animation, ideally inside one framed “operating canvas”.

### Stage 1: Source sweep

- Show 3-5 official procurement source cards.
- An arrow/cursor moves across them with short dwell states.
- One source card becomes active.

### Stage 2: Tender page open

- The active source expands or transitions into a tender page panel.
- The page should contain mixed Arabic/English text blocks or labels.
- Keep the page stylized but believable.

### Stage 3: Content scan

- A scanning band, highlight box, or reading rail moves across key content rows.
- Structured fields appear beside the source page:
  - title
  - entity
  - deadline
  - category
  - language signal

### Stage 4: Match evaluation

- A company profile panel becomes active.
- Show country scope, industry scope, and keyword/profile cues.
- The system should visually compare extracted tender attributes to profile attributes.

### Stage 5: Match outcome

- Display a matched state with clear reasons.
- Example visual outputs:
  - country matched
  - industry matched
  - keyword matched

### Stage 6: Delivery

- Emit an instant alert card or daily brief tile.
- Final state should feel like a handoff to a business team, not a celebration animation.

## Timing Guidance

- Whole loop: roughly 10-16 seconds if looping.
- Each state change should be readable without rushing.
- Use stagger only when it helps sequence understanding.

Suggested pacing:

- source sweep: 2.0-3.0s
- tender open: 1.0-1.5s
- scan/extract: 2.0-3.0s
- match: 1.5-2.5s
- alert emit: 1.0-1.5s
- rest state: 1.0-2.0s

## Interaction Guidance

- Hover can slightly pause or emphasize a state.
- Do not require hover for core understanding.
- Avoid autoplay video unless there is a strong reason. CSS/Framer Motion/state-driven animation is preferable.

## Reduced Motion Fallback

When reduced motion is enabled:

- Remove cursor travel.
- Remove scan sweeps.
- Keep one static multi-panel composition.
- Use subtle opacity reveals or no motion at all.
- Preserve the stage order with numbered labels or connecting arrows.

## Visual Style

- Cursor/arrow should look like a product operator tool, not a cartoon pointer.
- Highlight treatments should feel analytical and clean.
- Alerts should feel understated and trustworthy.
- No bouncing, elastic, celebratory, or confetti-like behavior.
