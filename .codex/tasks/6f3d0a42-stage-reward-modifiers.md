# Stage reward modifiers so card/relic effects preview before activation

## Summary
Reward selections append card/relic IDs to the party immediately, but their effects only apply when the next battle calls `apply_cards`/`apply_relics`. Players see nothing happen at selection time, missing the “Slay the Spire” style preview. We need a staging layer that previews the effect before commitment and then activates it cleanly.

## Details
* Selecting a card or relic writes the ID into the persisted party right away via `award_card`/`award_relic`, without invoking the corresponding `apply_*` logic.【F:backend/services/reward_service.py†L20-L148】【F:backend/autofighter/cards.py†L26-L38】【F:backend/autofighter/relics.py†L19-L50】
* Because modifiers activate during the next `setup_battle` call, players have no UI feedback that e.g. a relic granted HP or a card adjusted stats until they enter another fight.【F:backend/autofighter/rooms/battle/setup.py†L98-L138】

## Requirements
- Introduce a reward staging state that records pending card/relic effects separately from the active deck until the player confirms or preview animations complete.
- Emit rich metadata (stat deltas, upcoming triggers) so the frontend can show the preview before activation; coordinate with UI/UX for layout.
- Ensure activation happens exactly once when the player confirms (or when the next battle starts) and add tests covering duplicate prevention and persistence.
- Update documentation describing the new reward flow and how plugins can supply preview data.
