# Fix foe mitigation/vitality stack scaling in run start flow

## Problem
The run start flow currently records the `foe_mitigation` and `foe_vitality` modifier stacks with an additive value of `+0.00001` per stack. According to design feedback from Luna Midori, each stack should apply `+2.50` mitigation or vitality instead. The mismatch makes the stored modifier context almost zeroed out, causing downstream systems like the spawn pressure calculation and the autofighter foe factory to underpower stacked runs.

## Why this matters
* Spawn pressure and foe stat deltas in `backend/services/run_configuration.py` rely on the effective bonus captured in the modifier context. Using `0.00001` per stack effectively neuters these modifiers, invalidating balance assumptions when runs are resumed from their snapshot.
* The foe factory (`backend/autofighter/rooms/foe_factory.py`) applies `RunModifierContext.foe_stat_deltas` to live enemy stats. Values on the order of `0.00001` are imperceptible, so the feature fails silently for players.

## Requirements
* Update the modifier definitions for `foe_mitigation` and `foe_vitality` so their additive bonus is `+2.50` per stack before diminishing returns. Ensure the descriptive copy shown in the wizard matches the new scaling.
* Propagate the new per-stack value through any helper that exposes preview data or persists modifier snapshots (e.g., `_foe_modifier_effect`). Confirm the stored `effective_bonus` reflects the new scaling.
* Revisit spawn pressure tuning once the higher deltas are in place. If the new `+2.50` bonus destabilizes the pressure curve, adjust the mitigation/vitality weights so the resulting `foe_strength_score` stays within the intended range (1.0–5.0).
* Add or update regression coverage in `backend/tests/test_run_configuration_context.py` (or introduce a new test) to assert both modifiers report `+2.5` per stack in their effective bonus when no diminishing returns apply.
* Document the new scaling in the appropriate backend implementation notes (likely `backend/.codex/implementation/foe-scaling.md` or a related file) if those notes currently reference the old values.

## Definition of done
* The run start wizard snapshots show `+2.50` per stack for both modifiers, and the persisted modifier context records the expected additive bonus.
* Spawn pressure remains within the documented bounds after applying the revised bonuses (include reasoning or measurements in the PR notes/tests).
* Tests covering the modifier context pass with the new scaling.

## Implementation notes
* Updated `services/run_configuration.py` so mitigation and vitality modifiers grant +2.50 per stack before diminishing returns and adjusted spawn pressure weighting to keep foe strength within the intended range.
* Added regression coverage in `tests/test_run_configuration_context.py` verifying the new per-stack bonuses and spawn pressure clamping when diminishing returns are disabled.
* Documented the revised scaling in `.codex/implementation/run-configuration-metadata.md` and exercised the backend test suite with `uv run pytest tests/test_run_configuration_context.py`.

ready for review
