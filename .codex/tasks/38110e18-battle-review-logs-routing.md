Coder, surface the timeline review as both the post-battle overlay and a standalone `/logs/<run_id>` route.

## Context
- Once backend log endpoints exist, the frontend needs to hydrate the new timeline UI both after battles and when users open a shared logs link.

## Requirements
- Create a standalone frontend route (`/logs/[run_id]` or similar) that decodes query params for battle index, filters, comparison selections, and time window, restoring the captured state in the timeline UI.
- Update the overlay workflow to open the same timeline experience after a battle, reusing the stores/components introduced in the architecture task.
- Add a “Copy Logs Link” affordance in the overlay that serializes the current timeline state (metric tab, zoom range, filters, comparison set, pins) into URL-safe parameters compatible with the standalone route.
- Ensure reduced-motion settings, accessibility considerations, and authentication flows behave consistently between the overlay and the standalone page.
- Document the routing/shareable link behavior in the battle review implementation notes and add integration tests for the URL encoding/decoding flow.

## Notes
- Coordinate with the comparison/pins task so the serialized payload covers pin identifiers or future extensions as needed.
