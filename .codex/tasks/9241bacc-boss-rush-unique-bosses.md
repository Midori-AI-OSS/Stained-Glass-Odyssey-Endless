# Boss rush keeps reusing the same boss

## Summary
Boss rush runs currently spawn the exact same boss for every `battle-boss-floor` node on the floor. Players expect each boss encounter in the rush sequence to be unique, but the backend always reuses the first boss that was rolled.

## Technical background
* Boss rush floors are generated entirely out of `battle-boss-floor` nodes that all share the same `floor` and `loop` values. 【F:backend/autofighter/mapgen.py†L341-L379】
* When a boss room starts, `room_service._boss_matches_node` only compares the stored `floor_boss` metadata against the node's `floor` and `loop`. 【F:backend/services/room_service.py†L51-L60】
* Because every boss rush node matches those fields, `_boss_matches_node` returns `True` each time, `_instantiate_boss` re-creates the first boss, and the code never calls `_choose_foe` again. 【F:backend/services/room_service.py†L546-L557】
* The initial `floor_boss` snapshot is taken when the run starts (and again whenever a new floor is generated), so the same boss ID is persisted across the entire rush. 【F:backend/services/run_service.py†L240-L260】

## Impact
Every boss rush encounter is identical, defeating the purpose of the mode and removing the challenge/variety the mode promises. This is a regression from the normal floor flow, where only a single boss spawns at the end.

## Requested fix
Update the boss spawning logic so that boss rush nodes roll a fresh foe instead of reusing the persisted `floor_boss`. Potential approaches include tracking the last boss per node, including `room_id`/`index` in the `_boss_matches_node` comparison, or bypassing `floor_boss` reuse entirely when the run configuration is `boss_rush`. The fix should:

1. Allow each boss rush node to choose a new boss while still keeping restart safety for standard floor bosses.
2. Preserve the existing persistence behavior so resuming a run or re-entering the same node still loads the correct boss.
3. Include regression coverage (unit or integration) that demonstrates multiple distinct bosses appear across a single boss rush floor.
4. Document any changes to persistence logic or new state fields in the relevant `.codex/implementation` notes if needed.

## References
* `backend/services/room_service.py`
* `backend/services/run_service.py`
* `backend/autofighter/mapgen.py`

## Auditor findings (2025-03-19)
- ✅ Confirmed the implementation adds `index`/`room_id` matching so unique bosses are rolled per node and new regression tests cover the scenario.
- ❌ `uv run pytest tests/test_floor_boss_rotation.py` fails because `tests/conftest.py` seeds a stub `runs.lifecycle` module without the new `empty_reward_staging` export, causing an `ImportError` during collection. Extend the stub with the new attribute (and any other required helpers) so the suite can execute.
- ⚠️ The change adds new keys to the persisted `floor_boss` snapshot, but there is no accompanying update under `backend/.codex/implementation/` documenting the new schema. Please add the documentation called for in the task brief.

ready for review
