# Cache battle setup modifiers to remove redundant reapplication

## Summary
Every battle deep-copies the party, re-applies every learned card and relic, and then triggers each member’s `prepare_for_battle` hook. The combination with EventBus overhead makes battle setup balloon into multi-minute stalls. We need to cache persistent modifiers or incrementally apply changes so repeated battles don’t redo identical work.

## Details
* `setup_battle` clones party members and immediately calls `apply_cards` and `apply_relics`, forcing every plugin to emit setup events before combat can start.【F:backend/autofighter/rooms/battle/setup.py†L98-L138】
* `apply_cards`/`apply_relics` iterate the entire deck/relic list on every invocation, instantiating plugins afresh and calling `apply`, even when nothing changed since the previous fight.【F:backend/autofighter/cards.py†L26-L38】【F:backend/autofighter/relics.py†L19-L50】
* Reward selection simply appends IDs to `party.cards`/`party.relics`, so the same modifiers are recomputed on the next battle instead of being cached once when selected.【F:backend/services/reward_service.py†L20-L148】

## Requirements
- Design a caching or diff-based system (e.g., persist resolved stat modifiers or pre-built EffectManagers) so unchanged cards/relics don’t fully reapply each battle.
- Ensure stateful plugins that expect per-battle hooks still fire correctly (document how to opt into “always re-run” behavior if needed).
- Benchmark setup time before/after on a mid-game deck and record the improvement target (e.g., reduce setup to <5 s).
- Update documentation in `.codex/implementation` describing the new lifecycle, and add regression coverage that a newly acquired card still applies its effect the next fight.
