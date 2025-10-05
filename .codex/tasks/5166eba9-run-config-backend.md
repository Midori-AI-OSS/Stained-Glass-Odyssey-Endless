# Task: Implement Run Configuration Metadata Backend

## Summary
Build the backend plumbing for the run setup wizard described in the `Streamline Run Startup Workflow` goal. We already prune lingering runs on boot, but `start_run` still only understands party, damage type, and pressure. Coders need an API that advertises available run types and modifiers (pressure plus the new foe/player tuning knobs) and they must extend the run creation pipeline so selected options are validated, persisted, and surfaced for analytics.

## Prerequisites & References
- Goal file: `.codex/tasks/33e45df1-run-start-flow.goal`.
- Existing run creation service: `backend/services/run_service.py` (especially `start_run`).
- UI helper endpoints: `backend/routes/ui.py` for context on how run metadata is consumed today.
- Tracking hooks for logging selections: `backend/tracking` package.
- Follow repository standards in `AGENTS.md` and backend setup docs in `backend/README.md`.

## Detailed Requirements
1. **Metadata model and endpoint**
   - Define a canonical schema describing run types (e.g. Standard, Boss Rush) and stackable modifiers (pressure plus all foe- and player-facing knobs listed in the goal file).
   - Persist the metadata as structured data (JSON file, table, or module constant) that the service layer can load.
   - Implement a new `GET /run/config` (or similar) route under `backend/routes` that returns:
     - Available run types with identifiers, display names, descriptions, default modifier presets, and any constraints (e.g. allowed modifier ranges).
     - Modifier definitions including: identifier, label, category (foe-focused vs player-focused), stacking rules, numerical impact (e.g. foe HP increases by +0.5× per stack), diminishing-return behavior, and reward bonuses (e.g. +50% EXP/RDR for foe-focused stacks).
     - Explicit tooltip text for Pressure explaining encounter sizing, defense floors, elite odds, and shop tax scaling so the frontend can surface the math verbatim.
   - Ensure the metadata lives in a dedicated service module so tests can import it without hitting HTTP.

2. **Run creation updates**
   - Update `start_run` in `run_service.py` to accept `run_type` and `modifiers` payloads in addition to the current fields.
   - Validate that incoming selections exist in the metadata, respect allowed stack counts, and obey any per-run-type constraints. Provide clear error responses for invalid combinations.
   - Persist the chosen run type and modifier snapshot alongside the saved run state so future endpoints (map generation, analytics) can access it.
   - Adjust `MapGenerator` or related hooks only as needed to ensure modifier data is passed through; full gameplay effects can be follow-up work, but the baseline reward adjustments (+50% EXP/RDR per foe-focused stack, etc.) should be applied to stored run metadata so battle/reward services can read them.
   - Wire telemetry: include run type and modifiers in `log_run_start`, `log_menu_action` for the "Run started" event, and any other relevant analytics touchpoints.

3. **Supporting utilities and docs**
   - Add unit tests covering metadata loading, validation, and `start_run` error paths. Update existing tests to reflect the new request schema.
   - Document the schema and endpoint usage in `.codex/implementation` (e.g. update `game-workflow.md` or add a dedicated run configuration doc).
   - Confirm `.codex/tasks/33e45df1-run-start-flow.goal` is referenced in commit/PR notes as appropriate.

## Acceptance Criteria
- `GET /run/config` returns a comprehensive metadata payload covering run types, modifier definitions, reward impacts, and tooltip copy as described.
- `POST /run/start` rejects invalid run types/modifier stacks with descriptive errors and succeeds when selections match the metadata.
- Selected run type and modifier snapshot are persisted with the run and logged through existing telemetry utilities.
- Automated backend tests run via `uv run` (or `run-tests.sh`) cover new metadata logic and the extended `start_run` pathway.
- Documentation is updated to describe how the frontend should consume the new metadata and how backend services interpret stored modifiers.

## Coordination Notes
- Work with frontend owners so the API shape aligns with their wizard state machine.
- Surface any open questions (e.g. initial run type list, modifier caps) back to Task Master if blockers arise.
- Do **not** modify frontend code in this task; create follow-up tasks for UI work if necessary.

ready for review
