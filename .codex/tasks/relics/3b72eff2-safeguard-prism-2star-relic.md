# Safeguard Prism: reactive 2★ sustain spike

## Summary
Two-star relics emphasize counterattacks (Vengeful Pendant), first-action repeats (Echo Bell), or conditional damage spikes, but none shore up mid-battle survival spikes once Threadbare Cloak's shield is gone. We need a mid-tier option that prevents lethal swings when allies cross dangerous HP thresholds without overshadowing high-rank lifesavers. Safeguard Prism must now operate on a **turn-based cooldown** so it can re-trigger during protracted encounters without burning permanent charges.【F:.codex/implementation/relic-inventory.md†L21-L40】【F:.codex/planning/archive/bd48a561-relic-plan.md†L39-L50】

## Details
* Design **Safeguard Prism**: when an ally drops below 60% Max HP, immediately grant a shield worth ~15% Max HP per stack and a one-turn mitigation bonus (~12% per stack). Additional stacks still amplify the shield and mitigation, but **each ally must respect a five-turn cooldown, extended by +1 turn for every full five stacks** (5 stacks → 6 turns, 10 stacks → 7 turns, etc.).
* Track per-ally trigger cooldowns using the party state, reset on `battle_start`/`battle_end`, and piggyback on turn/round events (in addition to `damage_taken`) so cooldown expiry is detected reliably. Remember to enable overheal before applying shield healing so the barrier persists.【F:backend/plugins/relics/threadbare_cloak.py†L18-L38】【F:backend/plugins/relics/ember_stone.py†L27-L90】
* Surface detailed telemetry (`relic_effect`) capturing the HP threshold, shield size, and mitigation applied to aid debugging and replay logs.【F:backend/plugins/relics/guardian_charm.py†L20-L37】

## Requirements
- Implement `backend/plugins/relics/safeguard_prism.py` with the cooldown behavior above, including helper cleanup and a thorough `describe(stacks)` that spells out the base five-turn cooldown plus the +1 turn per five stacks scaling.
- Persist the last trigger turn per ally and hook into the appropriate BUS turn/round signals so cooldown expiry is tracked server-side (rather than burning stack counters).
- Expand backend tests to cover cooldown expiry, multi-stack timing, shield application (verifying overheal), and mitigation expiry. Add cases to `backend/tests/test_relic_effects.py` or a new focused module if clearer.
- Update `.codex/implementation/relic-inventory.md` and the relic design plan with the new cooldown mechanics and final tuning numbers.【F:.codex/implementation/relic-inventory.md†L21-L43】【F:.codex/planning/archive/bd48a561-relic-plan.md†L37-L63】
- Document any tuning rationale in `.codex/docs/relics/` if the mitigation math needs future reference.

---

## Auditor notes (2025-02-15)
- Core shielding logic fires on low-HP triggers, but implementation skips the required shield pipeline: it never enables overheal or calls `apply_healing`, instead mutating `target.shields` directly. That bypasses the diminishing-returns logic described in the requirements.
- Please switch to `target.enable_overheal()` + `safe_async_task(target.apply_healing(...))` so shields are generated through the standard helper, and make sure the minimum heal is enforced when Max HP is small.

## Follow-up required (2025-02-22 audit)
- 🔄 Rework the relic logic to use the five-turn (+1 per five stacks) cooldown instead of consuming a stack permanently per battle.
- 🔄 Update descriptive copy (`about`, `describe`, telemetry) and implementation docs/tests so they describe and validate the cooldown behavior.
- 🔄 Capture and expose turn-tracking data needed for the cooldown timer.
- 🔄 Fill in the missing Safeguard Prism prompt text in `luna_items_prompts.txt` so placeholder art tracking is accurate.
- 🔄 Ensure repository setup instructions (e.g., provide a `pyproject.toml` so `uv sync` works) cover backend dependencies for consistent environment bootstrap.

more work needed — pending cooldown redesign, docs/tests sync, and env manifest update
