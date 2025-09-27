# Battle Review Timeline

The refactored battle review view exposes an interactive timeline that rides on
`frontend/src/lib/components/battle-review/TimelineRegion.svelte` and the
supporting stores in `frontend/src/lib/systems/battleReview/state.js`.

## Data flow
- `createBattleReviewState` normalizes raw battle events into timeline buckets
  via `shapeTimelineEvents` and exposes the derived `timeline` store.
- Timeline data is loaded lazily through `loadEvents()`. The timeline component
  requests events on mount if the store is still idle so the graph stays in
  sync even when the drawer is closed.
- The shareable state encodes timeline filters (metric, entity ids, ability
  sources, event types, and reduced‑motion preference) so deep links reproduce
  the same view.

## TimelineRegion.svelte
- Provides the metric/entity/source/event filter bar and a zoom/offset control
  for constraining the active time window.
- Renders an SVG area chart for the aggregate metric and an overlay line for the
  focused entity (current tab). Highlights list the recent abilities that match
  the focus entity and respect the active filters.
- Scrubbing the chart or clicking highlight items updates the shared
  `timelineCursor` store so other consumers (event log) stay synchronized.
- Reduced motion (`filters.respectMotion`) disables visual transitions while
  still allowing keyboard and pointer interaction.

## EventsDrawer.svelte
- Draws from the filtered timeline projection rather than the raw events array
  so the log reflects the active filters and time window.
- Selecting an event jumps the cursor and highlights the matching entry in the
  timeline. When filters hide all events the drawer surfaces a contextual
  message (“No events matched the current filters”).

## Timeline metrics
`TIMELINE_METRICS` defines the available projections:

- `damageDone` – events sourced from damage dealing actions.
- `damageTaken` – targets taking damage.
- `healing` – active healing events and HoT ticks.
- `mitigation` – shields, temporary HP, and healing prevention.

Every metric captures a default colour, a role (attacker/target), and a list of
matching event types which keeps the timeline logic declarative and makes it
straightforward to add future projections.

## Testing notes
- The new tests in `frontend/tests/battle-review-timeline.test.js` cover metric
  aggregation, filter application, and the cursor setter to guard regressions.
- The events drawer no longer inspects the raw events array, so the timeline
  projection must remain stable under data transforms (tests enforce this by
  feeding synthetic events).
