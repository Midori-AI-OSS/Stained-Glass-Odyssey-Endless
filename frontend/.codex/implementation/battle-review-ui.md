# Battle Review Timeline Shell

The Battle Review overlay is now organized around a timeline-first layout backed by modular stores.

## Architecture Overview

- **State management** lives in `frontend/src/lib/systems/battleReview/state.js`. The exported `createBattleReviewState` helper fetches summaries and events, tracks loading status, derives overview metrics, and exposes the active tab/timeline data. Components access the state via the shared `BATTLE_REVIEW_CONTEXT_KEY` context.
- **`BattleReview.svelte`** sets up the state and renders the high-level header. It also owns the event-log toggle and pushes the state object into context for child components.
- **`TabsShell.svelte`** renders the metric tabs and composes the grid for the timeline viewport and per-entity metrics panel. The tab chips use `BattleReviewFighterChip.svelte`, which wraps the modern `BattleFighterCard` portrait so the battle review can share the same glow, motion, and cycling behaviors without maintaining a separate clone.
- **`TimelineRegion.svelte`** visualizes the most recent combat events in a scrolling list. It consumes the derived `timeline` store so it can update reactively once events finish streaming from the backend.
- **`EntityTableContainer.svelte`** handles both the overview aggregate presentation and the entity-specific breakdowns. It renders a stats side panel in addition to the central metrics tables to keep the new "side panel" design consistent with the timeline-first layout.
- **`EventsDrawer.svelte`** shows the raw event log when toggled. It subscribes to `eventsOpen` and lazily loads events when the drawer opens.

The timeline-first grid places metric tabs across the top, the timeline viewport on the left, and entity metrics/side panels on the right. The layout collapses gracefully for smaller viewports.

## Reduced Motion Handling

- The store exposes a `reducedMotion` derived store based on incoming props. Components consult this store when handing off reduced-motion preferences to portrait subcomponents or transitions.
- Tabs and portraits avoid hover animations when reduced motion is requested, and the event drawer skips transition effects entirely.

## Skip Battle Review Setting

Players can bypass the Battle Review screen entirely by enabling the **Skip Battle Review** toggle in the Gameplay settings tab (see [`settings-menu.md`](settings-menu.md)). When this setting is active, the post-battle summary is skipped and the game automatically advances to the next room after battle completion.
