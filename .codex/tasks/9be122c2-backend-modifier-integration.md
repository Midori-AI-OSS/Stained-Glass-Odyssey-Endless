# Task: Integrate Run Modifier Metadata Throughout Backend Systems

## Background
The run startup wizard now validates `run_type` and modifier stacks, persists a configuration snapshot on the run record, and sends telemetry with the chosen metadata. However, backend gameplay systems still use legacy pressure heuristics for map generation, foe scaling, and shop pricing, leaving the richer metadata unused during actual runs. To unlock end-to-end testing of modifier-driven runs, we need to thread the stored configuration through encounter generation, combatant instantiation, and economy logic.

Reference goal: `33e45df1-run-start-flow.goal`.

## Objectives
1. **Propagate configuration context**
   - Ensure `run_service.start_run` saves the normalized `configuration_snapshot` in the run state in a way that downstream systems (map generator, rooms, shops, foe factory) can easily access without relying on adhoc `getattr` checks.
   - Provide a helper that extracts modifier stack values and their effect metadata from the snapshot so rooms can request structured information (e.g., foe stat multipliers, shop multipliers, player stat penalties).

2. **Map generation & encounter assembly**
   - Update `MapGenerator` to consider modifier inputs such as foe spawn count bonuses and elite/glitched odds when constructing floor layouts. The configuration should adjust encounter pressure, optional room spawns (shops/rests), and boss rush overrides based on the snapshot instead of hard-coded `party` flags alone.
   - Extend `_desired_count` and related helpers inside `foe_factory.py` to honor foe-focused modifiers (HP, speed, mitigation, action cadence) when determining spawn counts and stat scaling. Replace the static `ROOM_BALANCE_CONFIG` multipliers with values computed from the configuration helper where applicable.

3. **Combatant instantiation**
   - When foes are instantiated, apply modifier-driven stat multipliers (HP, defenses, speed, damage) and diminishing returns using the metadata definitions in `backend/services/run_configuration.py`. Ensure modifiers with capped stacks or diminishing factors obey their rules.
   - Apply player-oriented modifiers during party preparation (e.g., stat penalties, mitigation, vitality boosts) so fights reflect the previewed difficulty changes.

4. **Shop economy integration**
   - Replace the current `1.26^pressure` pricing curve with modifier-aware calculations derived from the configuration snapshot. Support both stackable multipliers and tax overrides as defined in the metadata.
   - Surface modifier information in serialized shop payloads so the frontend can confirm active effects (e.g., metadata hash, relevant modifier summaries).

5. **Analytics & documentation**
   - Emit updated telemetry/tracking payloads that include any derived fields (e.g., effective foe HP multiplier, shop multiplier) to support analytics queries on modifier impact.
   - Update `.codex/implementation/game-workflow.md` (and any other affected docs) to describe the new backend behavior.

6. **Validation**
   - Add backend tests (unit or integration) covering map generation, foe factory scaling, shop pricing, and party stat adjustments under representative modifier stacks.
   - Extend existing frontend or API contract tests if necessary to confirm the backend responses expose the updated fields.

## Acceptance Criteria
- Map generation, foe encounters, and shop pricing demonstrably change when modifier stacks are varied, matching the metadata math used in the run wizard previews.
- All new behavior is backed by automated tests and reflected in documentation.
- Telemetry payloads capture the key derived values so analytics can monitor modifier usage and outcomes.
- No regression to boss rush shortcuts or legacy pressure-based flows (ensure fallback behavior when no modifiers are selected).
