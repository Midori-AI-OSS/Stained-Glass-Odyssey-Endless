## Bug: Glitched/Prime passives show twice in the WebUI

Goal: Reproduce and isolate why some characters (seen on Luna and Chibi) render two passive icons when their rank is glitched or prime.

### What we know
- Frontend passives are rendered in `frontend/src/lib/battle/BattleFighterCard.svelte` via `fighter.passives`.
- Passives are normalized in both `frontend/src/routes/+page.svelte` and `frontend/src/lib/systems/pollingOrchestrator.js` through a `mapStatuses` helper that maps `status.passives || f.passives || []`.
- Battle overlay combines statuses in `frontend/src/lib/components/BattleView.svelte` (`combineStatuses` builds chips from `unit.passives`).
- Backend tier resolution stacks variants for multi-tag ranks: `backend/autofighter/passives.apply_rank_passives` calls `resolve_passives_for_rank`, which returns glitched/prime/boss variants cumulatively (glitched prime boss yields multiple IDs).
- Tier system doc: `.codex/implementation/tier-passive-system.md` (explicitly allows stacking multiple tier variants).

### Suspected duplication vectors
- New tier loader may be returning both base and tier variants, or both glitched+prime variants for a single foe, causing two UI entries.
- Battle snapshots might carry both `passives` and `status.passives`, and the normalization step could be merging in a way that preserves duplicates (e.g., base roster passives plus battle-status passives).
- Keying in `BattleFighterCard` uses `p.id`, so two entries with the same `id` from different sources will both render; confirm whether duplication is identical IDs or distinct tier IDs.

### How to reproduce
1) Force/observe a battle with glitched or prime variants of Luna or Chibi (user saw duplicates there). Any foe/party member with rank tags should work.
2) Watch the battle portraits in the WebUI and note if two passive icons appear for a single character when only one should.
3) Capture a battle snapshot payload (UI poll) to see the `passives` array contents for that entity; look for base + tier or multiple tier variants.

### Suggested investigation steps
- Inspect snapshot shaping: trace from backend battle payload through `mapStatuses` in `+page.svelte` and `pollingOrchestrator.js` to `BattleView` and `BattleFighterCard`.
- Check if `PassiveRegistry.describe` output is used anywhere in the live snapshot (battle snapshots may differ from initial party info). Confirm whether battle snapshots already include tier-resolved passives.
- Verify whether rank-tag stacking (glitched prime) is intended to render multiple passive indicators; reconcile with design in `.codex/implementation/battle-view.md` (expects per-passive pips/spinner/number).
- Determine if duplicate icons are identical IDs (e.g., `luna_lunar_reservoir` twice) or distinct tier IDs (`_glitched`, `_prime`) and whether that matches intended stacking.

### Deliverable
- Root cause write-up: where duplication enters the pipeline (backend payload vs frontend normalization vs rendering).
- Recommendation: whether to dedupe, change backend payload, or keep stacking (if intentional) and adjust UI copy.
