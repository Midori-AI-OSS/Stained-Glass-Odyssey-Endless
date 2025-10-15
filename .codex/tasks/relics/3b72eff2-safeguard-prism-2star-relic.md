# Safeguard Prism: reactive 2★ sustain spike

## Summary
Two-star relics emphasize counterattacks (Vengeful Pendant), first-action repeats (Echo Bell), or conditional damage spikes, but none shore up mid-battle survival spikes once Threadbare Cloak's shield is gone. We need a mid-tier option that prevents lethal swings when allies cross dangerous HP thresholds without overshadowing high-rank lifesavers.【F:.codex/implementation/relic-inventory.md†L21-L40】【F:.codex/planning/archive/bd48a561-relic-plan.md†L39-L50】

## Details
* Design **Safeguard Prism**: when an ally drops below 60% Max HP for the first time in a battle (per stack), immediately grant a shield worth ~15% Max HP per stack and a one-turn mitigation bonus (~12% per stack). Additional stacks should allow multiple trigger charges per ally (one per stack) to reward investment.
* Track per-ally trigger counts using the party state, reset on `battle_start`/`battle_end`, and piggyback on `damage_taken` events like other reactive relics do. Remember to enable overheal before applying shield healing so the barrier persists.【F:backend/plugins/relics/threadbare_cloak.py†L18-L38】【F:backend/plugins/relics/ember_stone.py†L27-L90】
* Surface detailed telemetry (`relic_effect`) capturing the HP threshold, shield size, and mitigation applied to aid debugging and replay logs.【F:backend/plugins/relics/guardian_charm.py†L20-L37】

## Requirements
- Implement `backend/plugins/relics/safeguard_prism.py` with the behavior above, including helper cleanup and a thorough `describe(stacks)` explaining trigger counts, shield size, and mitigation.
- Expand backend tests to cover multi-stack triggers, single-battle limits, shield application (verifying overheal), and mitigation expiry. Add cases to `backend/tests/test_relic_effects.py` or a new focused module if clearer.
- Update `.codex/implementation/relic-inventory.md` and the relic design plan with Safeguard Prism's final numbers and intent.【F:.codex/implementation/relic-inventory.md†L21-L43】【F:.codex/planning/archive/bd48a561-relic-plan.md†L37-L63】
- Provide a placeholder icon under `frontend/src/lib/assets/relics/2star/` and ensure the catalog/tooltip surfaces the description via the usual metadata plumbing (no custom frontend code expected beyond verifying the asset loads).【F:frontend/src/lib/systems/assetRegistry.js†L174-L1353】
- Document any tuning rationale in `.codex/docs/relics/` if the mitigation math needs future reference.
