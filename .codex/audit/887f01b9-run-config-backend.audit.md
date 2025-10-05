# Audit Report: Run Configuration Backend Task

## Summary
The backend implementation introduces run configuration metadata, validation logic, and telemetry hooks, but several deliverables from task `5166eba9-run-config-backend` remain incomplete or incorrect. The issues below block the task from meeting its acceptance criteria and prevent the frontend wizard described in the paired goal from functioning as specified.

## Findings

### 1. Metadata endpoint omits required modifier effect details (**Major**)
The task requires the metadata payload to include stacking rules, numerical impacts, diminishing-return behaviour, and reward bonuses so the frontend can surface the math verbatim.【F:.codex/tasks/5166eba9-run-config-backend.md†L13-L37】 However, `get_run_configuration_metadata` only exposes basic fields (id, label, category, min stacks, stack step, reward flag) and a tooltip for Pressure; none of the per-stack numbers or diminishing-return details are returned.【F:backend/services/run_configuration.py†L233-L255】 As written, the frontend cannot display the information mandated by the goal.

### 2. Character Stat Down rewards do not match the specification (**Major**)
The goal states that Character Stat Down should grant a 5% RDR/EXP bonus on the first stack and +1% per additional stack, citing two stacks = 11%.【F:.codex/tasks/33e45df1-run-start-flow.goal†L21-L46】 The `_character_stat_penalty` helper instead computes `0.05 + (stacks - 1) * 0.01`, yielding 6% at two stacks.【F:backend/services/run_configuration.py†L109-L128】 This diverges from the documented scaling and will mislead both tooltips and reward math.

### 3. `/ui/action` start_run handler ignores new configuration fields (**Major**)
Although `start_run` now accepts `run_type` and `modifiers`, the `/ui/action` pathway still forwards only party, damage type, and pressure, making it impossible for the existing UI client to send the new configuration data.【F:backend/routes/ui.py†L318-L336】 The task explicitly called for extending `start_run` support for these fields so the UI could consume the metadata endpoint.【F:.codex/tasks/5166eba9-run-config-backend.md†L23-L39】 Without updating this handler (or documenting a required client switch to `/run/start`), the wizard flow cannot launch configured runs.

### 4. Documentation deliverable missing (**Moderate**)
Task guidance requires documenting the schema and endpoint usage in `.codex/implementation` (e.g., by updating `game-workflow.md` or adding a dedicated doc).【F:.codex/tasks/5166eba9-run-config-backend.md†L30-L40】 No such update exists; `game-workflow.md` still describes the legacy single-step run start flow with no mention of run types, modifiers, or the new endpoints.【F:.codex/implementation/game-workflow.md†L1-L46】 This leaves the knowledge base out of sync with the code.

### 5. Missing automated coverage for the new start_run pathways (**Moderate**)
The task asks for tests covering metadata loading, validation, and the extended `start_run` error paths.【F:.codex/tasks/5166eba9-run-config-backend.md†L30-L40】 The added test module exercises only metadata shape and `validate_run_configuration`; there are no assertions that `start_run` stores configuration snapshots, applies reward bonuses, or rejects invalid selections.【F:backend/tests/test_run_configuration_service.py†L1-L34】 Additional unit tests are needed to meet the requirement and protect the new behaviour.

## Recommendations
Address the issues above before approving the task:
- Expand the metadata payload to include per-modifier effect data (e.g., per-stack bonuses, diminishing factors, reward bonuses) so the frontend can present accurate tooltips.
- Correct the Character Stat Down reward curve to match the documented 5% + 6% (or clarify/update the documentation if the intended numbers differ).
- Update the `/ui/action` handler (or formally retire it) so clients can pass `run_type` and `modifiers` through the primary UI API.
- Update `.codex/implementation` documentation with the new schema/endpoints.
- Add `start_run`-level tests that cover success and validation failures with the new configuration fields.

Until these gaps are resolved, the backend does not fully support the run setup wizard described in the goal file.
