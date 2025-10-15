# Audit: Rusty Buckle threshold clarification task

## Task
- `.codex/tasks/relics/1e2c2fc3-fix-rusty-buckle-threshold.md`

## Findings
1. ✅ `backend/plugins/relics/rusty_buckle.py` now documents the intentional 50× (5000%) HP-loss multiplier directly above `_threshold_multiplier`, clarifying the design for future readers.【F:backend/plugins/relics/rusty_buckle.py†L205-L214】
2. ✅ The implementation docs have been corrected: the `Rusty Buckle` entry now spells out that volleys require losing 50× (5000%) of party Max HP per stack, adding another 10× / 1000% per extra stack.【F:.codex/implementation/relic-inventory.md†L13-L15】
3. ✅ `.codex/docs/relics/rusty-buckle-threshold-notes.md` now lives with the rest of the relic documentation, records the 5000% rationale, and cross-links back to the inventory reference and implementation comment so the relocation remains discoverable.【F:.codex/docs/relics/rusty-buckle-threshold-notes.md†L1-L25】
4. ✅ The task record reflects the completed audit, pointing reviewers at the relocated design note under `.codex/docs/relics/` and confirming the 50× / 5000% math is fully documented.【F:.codex/tasks/relics/1e2c2fc3-fix-rusty-buckle-threshold.md†L1-L23】

## Verdict
All blocking findings are resolved. The implementation docs and supporting design note now document the intentional 50× / 5000% threshold, and the design rationale lives with the rest of the relic docs, so the task can proceed to review.
