Coder, add comparison workflows and pin/bookmark support to the battle timeline.

## Context
- Analysts need to compare multiple party members or foes and bookmark important windows, features missing from the current Battle Review design.

## Requirements
- Enable selecting multiple entities to overlay their timeline datasets and per-entity tables, including clear UI affordances for adding/removing comparisons.
- Persist comparison selections during a review session so users can switch tabs without losing context.
- Introduce a pins/bookmark system that captures the current time window, filters, metric tab, and comparison set; display saved pins in a sidebar list.
- Allow users to rename, reorder, and delete pins, and ensure selecting a pin restores the captured state across the timeline, tables, and events log.
- Document the comparison and pin UX in the battle review implementation notes and add component tests for pin serialization/restoration logic.
- Keep comparison overlays and pin restoration deterministic so that identical datasets and timestamps reproduce the same orderi
  ng/state; cover this with automated tests to protect shareable links and QA workflows.

## Notes
- Coordinate with the shareable logs task so pin payloads can be encoded into overlay events or URLs later.
