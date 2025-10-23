# Add 4★ card: Supercell Conductor themed after LadyStorm

## Summary
Create a four-star reward that captures LadyStorm's slipstream-and-burst gameplay by chaining bonus actions for Wind and Lightning allies. The effect should offer proactive tempo without duplicating Overclock's global double turn.

## Design requirements
- Title the card **Supercell Conductor** and register it at the 4★ rarity.
- Base bonuses: **+240% ATK** and **+240% Effect Hit Rate** to amplify aggressive hybrid casters.
- Passive effect:
  - At battle start and every **third round** thereafter, grant the fastest Wind or Lightning ally a **Tailwind** buff.
  - Tailwind immediately grants a bonus action at **50% damage** and **+30% Effect Hit Rate** for that action only.
  - After the bonus action resolves, apply **-10% Mitigation** to all enemies hit for 1 turn to set up follow-up bursts.
- Ensure the round counter respects the battle loop so the cadence is predictable (start of rounds 1, 4, 7, ...).

## Implementation notes
- Add the new plugin under `backend/plugins/cards/`, hooking into round start triggers and selecting the appropriate ally via initiative stats.
- Implement the Tailwind bonus action by leveraging the existing extra-action utilities used by Swift Footwork, but scope it to the chosen ally and reduced damage.
- Mitigation shred should reuse existing debuff helpers and expire at the next turn start.
- Update `.codex/implementation/card-inventory.md` and `.codex/planning/archive/726d03ae-card-plan.md` with the card details, and adjust any UI copy if the cadence needs clarification.
- Expand tests for 4★ cards to cover Tailwind scheduling, damage scaling, and mitigation debuff application.

## Deliverables
- Functional Supercell Conductor plugin with stat bonuses, Tailwind cadence, and mitigation debuff handling.
- Documentation updates enumerating the new card and clarifying its timing windows.
- Automated test coverage verifying the round-based trigger and reduced-damage action.

## Player impact
Supercell Conductor supplies Wind/Lightning lineups with periodic tempo spikes that soften enemy defenses, supporting aggressive combo lines distinct from Overclock's global action flood.
