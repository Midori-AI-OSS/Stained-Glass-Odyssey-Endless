# Clarify Rusty Buckle HP-loss multiplier intent

## Summary
Rusty Buckle intentionally multiplies party Max HP by `50.0` per stack when determining when to trigger the Aftertaste volley, yielding "5000%" progress at one stack. However, some contributors assume this value represents 50%, leading to repeated attempts to "fix" the math.

## Details
* `_threshold_multiplier` returns `50.0 + 10.0 * (stacks - 1)` and is reused for both charge accumulation and the player-facing description.【F:backend/plugins/relics/rusty_buckle.py†L205-L223】
* This multiplier is intended to be 50× (5000%), not 50%, so the relic should continue using the current math.
* Documentation and comments currently fail to explain this design choice, which is causing confusion and churn in task tracking.
* `.codex/docs/relics/rusty-buckle-threshold-notes.md` records the rationale behind the oversized threshold so design intent is preserved.【F:.codex/docs/relics/rusty-buckle-threshold-notes.md†L1-L18】

## Requirements
- Update the relevant relic documentation (create or extend the appropriate `.codex/implementation` reference) to explicitly call out that Rusty Buckle's thresholds are expressed as 50× / 5000% of party Max HP per stack.【F:.codex/implementation/relic-inventory.md†L13-L15】
- Add in-line comments or docstrings near `_threshold_multiplier` clarifying that the large percentage is intentional and by design.
- Note the rationale in any applicable design notes or changelog so future contributors understand that 5000% is not a bug.【F:.codex/docs/relics/rusty-buckle-threshold-notes.md†L1-L18】

ready for review

Audit: approved – design notes now reside under `.codex/docs/relics/`, and the 50× / 5000% threshold rationale is documented alongside the updated implementation references.
