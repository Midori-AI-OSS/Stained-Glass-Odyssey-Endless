# Battle Review Timeline Shell

The Battle Review overlay is now organized around a timeline-first layout backed by modular stores.

## Architecture Overview

- **State management** lives in `frontend/src/lib/systems/battleReview/state.js`. The exported `createBattleReviewState` helper fetches summaries and events, tracks loading status, derives overview metrics, and exposes the active tab/timeline data. Components access the state via the shared `BATTLE_REVIEW_CONTEXT_KEY` context.
- **`BattleReview.svelte`** sets up the state and renders the high-level header. It also owns the event-log toggle and pushes the state object into context for child components.
- **`TabsShell.svelte`** renders the metric tabs and composes the grid for the timeline viewport and per-entity metrics panel.
- **`TimelineRegion.svelte`** visualizes the most recent combat events in a scrolling list. It consumes the derived `timeline` store so it can update reactively once events finish streaming from the backend.
- **`EntityTableContainer.svelte`** handles both the overview aggregate presentation and the entity-specific breakdowns. It renders a stats side panel in addition to the central metrics tables to keep the new "side panel" design consistent with the timeline-first layout.
- **`EventsDrawer.svelte`** shows the raw event log when toggled. It subscribes to `eventsOpen` and lazily loads events when the drawer opens.

The timeline-first grid places metric tabs across the top, the timeline viewport on the left, and entity metrics/side panels on the right. The layout collapses gracefully for smaller viewports.

## Shareable Logs Routing

- The Battle Review shell is also exposed as a standalone route at `/logs/[run_id]`. The page hydrates the review by parsing URL parameters (battle index, active tab, timeline filters, comparison selections, pins, and zoom window) with the helpers in `battleReview/urlState.js` and passing them to the shared stores.
- The route keeps the query string in sync with in-app changes by listening for the `statechange` event emitted from `BattleReview.svelte`. Navigation is performed with `goto(..., { replaceState: true })` so browser history stays tidy when filters change.
- The overlay now includes a **Copy Logs Link** button that serializes the current state into URL-safe params via `buildBattleReviewLink`. Links always target `/logs/[run_id]` and encode the tab, filters, comparison set, pins, and zoom range so the standalone page restores the same view.
- Reduced-motion and accessibility behavior match the in-game overlay by reusing settings from `motionStore` when the standalone route mounts and by mirroring the overlay header semantics.

## Reduced Motion Handling

- The store exposes a `reducedMotion` derived store based on incoming props. Components consult this store when handing off reduced-motion preferences to portrait subcomponents or transitions.
- Tabs and portraits avoid hover animations when reduced motion is requested, and the event drawer skips transition effects entirely.

## Skip Battle Review Setting

Players can bypass the Battle Review screen entirely by enabling the **Skip Battle Review** toggle in the Gameplay settings tab (see [`settings-menu.md`](settings-menu.md)). When this setting is active, the post-battle summary is skipped and the game automatically advances to the next room after battle completion.
