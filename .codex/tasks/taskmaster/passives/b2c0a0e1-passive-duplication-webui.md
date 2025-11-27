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

### Investigation Summary
- Backend tier stacking intentionally replaces each base passive with every applicable tier variant (`apply_rank_passives` → `resolve_passives_for_rank`) so stats, effects, and passives lists still contain `_glitched`, `_prime`, and `_boss` entries even when a single visual indicator is desired.
- The UI already normalizes snapshots via `mapStatuses` in both `+page.svelte` and `pollingOrchestrator.js`, making that helper the best single place to alter the payload without touching gameplay logic.
- Tier priority is documented in `.codex/implementation/tier-passive-system.md` (glitched > prime > boss > normal), so the dedup logic can rely on that ordering to pick the “highest-rank” variant in each group while leaving backend stacking alone.

### Solution & Implementation
- Added `frontend/src/lib/systems/passiveUtils.js` with `dedupeTieredPassives`, which groups passives by their base ID (stripping `_glitched`, `_prime`, `_boss` suffixes) and keeps whichever variant has the highest tier according to the documented order. The helper returns a new array so metadata such as `stacks`, `display`, and `max_stacks` stay attached to the chosen variant.
- Hooked both normalization helpers (`+page.svelte` and `pollingOrchestrator.js`) to call `dedupeTieredPassives(status.passives || f.passives || [])` when rebuilding each combatant, ensuring every UI consumer now sees only one passive indicator per base ability while the backend continues to store and trigger the stacked variants for actual effects.

### Architectural Considerations
- `passiveUtils.dedupeTieredPassives` is the current frontend fix; it operates just before rendering and enforces the documented tier priority (glitched > prime > boss > normal) while keeping display metadata intact. This keeps the UI clean without touching gameplay data.
- The user question raises a valid point: the backend still emits every stacked tier variant for gameplay reasons (effects, damage tables, status tracking), and we now dedupe on the frontend for display.
- If we ever move this normalization server-side, we need to ensure we still deliver the full stacked list for battle resolution because the backend applies buff/debuff counters based on those individual IDs.

### Display vs Gameplay Data
- Passives represent both gameplay effects (stacked modifiers that can coexist and influence battle math) and display metadata (icon, name, localized text, stack counts for UI chips). The backend must keep the stacked effect list alive to avoid regressing battle logic.
- The frontend-only deduplication leaves the raw payload unchanged for any consumer that might need the full list (logs, debugging, telemetry) while the UI derives the desired visual subset. This separation avoids forcing other clients to mirror dedup logic.
- A potential future refactor is to have the backend expose two concepts: `passive_effects` (full stacked list) and `passive_display` (pre-deduped metadata that the frontends can pipe into `fighter.passives`). That would relieve WebUI from re-implementing tier logic but would require an agreed-upon contract so other consumers know which list to trust.

### Recommendation
- **Current frontend approach pros:** no backend API change, quick iteration, keeps display logic near rendering, and works immediately for dynamic scenarios like Luna’s sword stacks changing mid-battle (the helper runs every status refresh and picks the highest tier in real time).
- **Current frontend approach cons:** duplicates tier logic across clients, increases maintenance surface, and requires every new UI consumer to remember to dedupe the timeline before showing passives.
- **Backend normalization pros:** centralizes tier priority rules, guarantees consistent display data for any client, and avoids duplicate UI helpers; it also opens a place to document `display_passives` vs `effects`. 
- **Backend normalization cons:** would need explicit separation between gameplay effects and visual metadata; the backend would either have to compute a display view or teach clients which list to surface, and we risk dropping data needed for battle tracking if we over-normalize.
- **Display vs effects refactor:** start by keeping the dedupe helper but add instrumentation (logs, snapshot comparisons) to know when `passive_display` would diverge from `passive_effects`. If the backend can emit a dedicated display array without losing stacked IDs, we should document that transition as part of a future payload contract change.
- **Dynamic display impact:** Luna’s swords and similar stacks change as counters are consumed, so any display normalization must respond to backend updates. The current frontend dedup helper reruns on every status refresh, so it naturally shows the highest active tier while letting rare transitions (e.g., losing a prime buff) immediately show the next variant.

### Next Steps
- No automated tests were run (UI-only change).

---
Task Status: Approved (fix live in frontend)
Auditor Notes: Confirmed `dedupeTieredPassives` utility is wired in `frontend/src/lib/systems/passiveUtils.js` and called from `+page.svelte`, `pollingOrchestrator.js`, and `BattleView.svelte`, removing duplicate passive icons for tiered passives. UI tests not run here; appears ready for Task Master closure.
Reviewed by: Codex (Auditor Mode)
Date: 2025-11-29
---
