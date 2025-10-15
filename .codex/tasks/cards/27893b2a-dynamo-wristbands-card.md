# Add 1★ card: Dynamo Wristbands for Ixia-centric lineups

## Summary
Design and implement a new one-star card that leans into Ixia's lightning bruiser theme while keeping the effect appropriately modest for the rarity tier. The reward should provide a small offensive bump and encourage players to mix lightning dealers with crit-focused builds without eclipsing existing 1★ staples.

## Design requirements
- Name the card **Dynamo Wristbands** and classify it as a 1★ reward.
- Baseline bonus: **+3% ATK** to mirror other low-tier offensive cards.
- Unique passive: whenever an ally deals **Lightning** damage (including basic attacks or skill effects tagged to the lightning element), grant that ally **+3% Crit Rate for 1 turn**, stacking up to **2 times**.
- Ensure the effect respects existing turn/stack cleanup rules so the crit rate buff expires correctly when the duration ends.

## Implementation notes
- Add a new plugin under `backend/plugins/cards/` that extends the common card base and hooks lightning damage events without blocking other elements.
- Verify the element check aligns with the damage type plumbing described in `.codex/implementation/stats-and-effects.md`.
- Update inventory and planning docs so the new reward appears alongside other 1★ entries (`.codex/implementation/card-inventory.md`, `.codex/planning/archive/726d03ae-card-plan.md`).
- Extend any unit tests that enumerate 1★ cards (see `backend/tests` coverage for card registration) so Dynamo Wristbands is included.

## Deliverables
- New card plugin with metadata, star rank, stat bonus, and triggered buff logic.
- Doc updates covering the new card in both the live inventory reference and the planning document.
- Passing backend tests relevant to card registration and reward rolls.

## Player impact
Adding a lightning-centric 1★ option expands early-run build variety by letting players chase bonus crit uptime when they roll Ixia, LadyLightning, or other lightning specialists, while still offering a straightforward stat bump for general parties.
