# Task: Implement Run Startup Wizard

## Context
- The run configuration metadata API at `/run/config` now exposes run types, modifiers, and tooltip copy that the frontend does not yet consume.【F:backend/routes/ui.py†L520-L590】【F:backend/services/run_configuration.py†L340-L412】
- `start_run` persists the selected run type, modifiers, and pressure, but the UI still posts legacy payloads from the minimal `RunChooser` overlay.【F:backend/services/run_service.py†L120-L260】【F:frontend/src/lib/components/RunChooser.svelte†L1-L69】【F:frontend/src/lib/systems/uiApi.js†L1-L90】
- Telemetry hooks capture run start events, yet the wizard flow and modifier analytics described in the goal remain unimplemented.【F:backend/services/run_service.py†L205-L260】【F:.codex/tasks/33e45df1-run-start-flow.goal†L1-L63】

## Objective
Replace the single-step run start interaction with a resilient multi-step wizard that consumes live metadata, records user intent, and lays groundwork for analytics and future configuration hooks.

## Requirements
1. **Wizard Flow & State Management**
   - Replace `RunChooser` with a multi-step wizard that sequences: party builder → run type selection → modifier configuration → confirmation/start.
   - Handle cancellation, back navigation, resume-after-error states, and accessibility (keyboard traversal + screen reader announcements).
   - Ensure the overlay routing removes the old single-click start entry points once the wizard ships.
2. **Metadata Consumption & Posting**
   - Fetch `/run/config` metadata on wizard entry, cache it client-side, and surface modifier descriptions, tooltips, and reward previews.
   - Post the full configuration (`run_type`, `modifiers`, `pressure`, party composition) through the UI API and persist client defaults for future launches.
   - Validate backend responses and display errors inline when selections become invalid or the metadata changes mid-session.
3. **Telemetry & Analytics Hooks**
   - Extend frontend logging so each wizard step emits impressions and adjustments.
   - Confirm backend telemetry (`log_run_start`, `log_menu_action`, or equivalents) records the enriched payload; document any missing events as follow-up tasks.
4. **Documentation & Tests**
   - Update relevant `.codex/implementation` docs to describe the wizard UX and metadata contract.
   - Add automated coverage for the wizard state machine (frontend) and new backend validation cases.

## Deliverables
- Updated frontend components/stores implementing the wizard and metadata rendering.
- Backend/UI API changes (if needed) to accept and validate the expanded payload.
- Telemetry updates plus a short note summarizing any analytics follow-ups required.
- Documentation updates covering the new flow, plus tests demonstrating happy path and failure handling.

## Success Criteria
- Launching a run always passes through the wizard, persists selections, and survives refresh/resume scenarios.
- Players can preview modifier effects and pressure math before confirming.
- Analytics receives the enriched run configuration and wizard interaction events.
- No regressions to existing run start/resume flows (document manual test plan for QA).

## References
- `.codex/tasks/33e45df1-run-start-flow.goal`
- `backend/services/run_service.py`
- `backend/routes/ui.py`
- `backend/services/run_configuration.py`
- `frontend/src/lib/components/RunChooser.svelte`
- `frontend/src/lib/systems/uiApi.js`

ready for review
