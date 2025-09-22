Coder, redesign the Battle Review into an FFLogs-style timeline analysis surface.

## Context
- `frontend/src/lib/components/BattleReview.svelte` currently renders tab buttons, summary tables, and a modal toggle for raw events, but it lacks timeline graphs, metric tabs, or deep filtering similar to FFLogs. The implementation glues together summary fetches and per-entity panels within a monolithic component, making larger visualizations difficult to add.【F:frontend/src/lib/components/BattleReview.svelte†L1-L200】【F:frontend/src/lib/components/BattleReview.svelte†L340-L520】
- The Battle Review documentation still describes a static three-column layout driven by `LegacyFighterPortrait`, with no mention of timeline playback, comparison, or query controls.【F:frontend/.codex/implementation/battle-review-ui.md†L1-L13】
- OverlayHost mounts BattleReview as a fullscreen popup after each fight, so any new analysis view must continue to integrate with the existing overlay lifecycle and respect reduced-motion settings.【F:frontend/src/lib/components/OverlayHost.svelte†L372-L398】

## Requirements
- Replace the current Battle Review layout with a timeline-first interface inspired by FFLogs: metric tabs across the top (Damage Done, Damage Taken, Healing, etc.), a query/filter bar, a synchronized fight timeline graph, per-entity tables, and a dedicated events log.
- Implement an interactive timeline visualization that can zoom to specific windows, scrub along the fight, and highlight ability usage for the selected player, foe, or filter.
- Add comparison workflows that allow selecting multiple entities (e.g., two party members) and overlaying their timelines/tables to highlight rotation differences. Persist comparison selections within the review session.
- Build a pins/bookmark system so users can save a filtered view (time window + filters + metric) and jump back to it quickly; ensure pins can be shared via overlay events or copied links once backend routing supports it.
- Introduce modular stores/utilities under `frontend/src/lib/systems/battleReview/` to manage fetched summaries, events, and derived timeline datasets so the Svelte components stay focused on presentation.
- Ensure the events log supports fast searching, type filtering (damage, healing, buffs, mitigations), and jumping the timeline playback to the selected timestamp.
- Integrate reduced-motion handling so graph animations, scrubbing highlights, and transitions respect the animation token work (task 4e7a2427) and granular motion settings.
- Update or replace `frontend/src/lib/components/battle-review/` subcomponents with timeline-aware equivalents (graphs, tables, comparison panel) and delete obsolete files once migrated.
- Refresh documentation (`frontend/.codex/implementation/battle-review-ui.md`, plus any new module docs) to describe the timeline system, query controls, comparison flows, and pinning UX.
- Provide unit or component coverage for the new stores (data shaping, filtering) and interaction-heavy components (timeline syncing, comparison toggles) to keep regressions visible.
- Expose shareable battle logs by adding a `GET /logs/<run_id>` backend route (and `GET /logs/<run_id>/battles/<index>/{summary,events}`) that mirrors the existing active-run endpoints but works for completed runs; include battle start/end timestamps, participants, and file-backed links in the response so the frontend can list available encounters and hydrate a dedicated playback view.
- Surface the new timeline review as both the post-battle overlay and a standalone `/logs/<run_id>` route in the frontend, decoding query params for battle index, filters, comparison selections, and time window so copied links jump straight into the intended view (this frontend URL is what should be shared/bookmarked and referenced elsewhere).
- Add a “Copy Logs Link” affordance in the overlay that serializes the current metric tab, zoom range, filters, and comparison set into query parameters compatible with the standalone logs page so users can easily revisit past battles via the frontend URL.
- When wiring up the tracking database (task `5aa0a6dd-run-history-database`), include a `logs_url` field in run history responses that points to the frontend playback route (`/logs/<run_id>`) and defer raw combat data to the filesystem-backed log endpoints rather than duplicating it in SQLCipher.

## Notes
- Coordinate with backend/API owners if additional data is required (e.g., positioning, timestamps, mitigations). Document interim stubs if full parity needs multiple milestones.
- Aim for deterministic rendering so pins and comparison views stay shareable across sessions.

Task ready for implementation.
