Coder, implement the interactive battle timeline visualization and advanced filtering.

## Context
- The refactored Battle Review layout needs a timeline graph, metric tabs, and an events log that can drive analysis similar to FFLogs, but none of these interactions exist yet.【F:frontend/src/lib/components/BattleReview.svelte†L200-L339】

## Requirements
- Build a zoomable/scrubbable timeline visualization that synchronizes with the selected metric tab (Damage Done, Damage Taken, Healing, etc.) and highlights abilities for the focused entity.
- Implement a query/filter bar that can constrain timeline data by entity, ability type, time window, and reduced-motion preferences, updating the graph and tables in real time.
- Enhance the events log so selecting an event jumps the timeline playback to the corresponding timestamp and filters respect the query bar state.
- Respect reduced-motion settings by disabling heavy animations and providing accessible focus states for keyboard navigation.
- Cover the timeline data shaping, filtering, and interaction handlers with unit/component tests.
- Update the battle review documentation to describe the timeline visualization, metric tabs, and filtering UX.

## Notes
- Coordinate with the data stores task so the timeline component can consume pre-shaped datasets efficiently.
