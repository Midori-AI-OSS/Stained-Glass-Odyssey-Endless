# Add 5★ card: Equilibrium Prism echoing Ryne's balance theme

## Summary
Ship a top-tier five-star reward centered on Ryne's balance mechanic, giving late-game teams a strategic redistribution tool rather than raw damage. The card should fundamentally alter party flow, competing with existing 5★ powerhouses.

## Design requirements
- Name the card **Equilibrium Prism** and classify it as a 5★ card.
- Base bonuses: **+1500% ATK** and **+1500% DEF** to underscore the late-game power spike.
- Passive effect sequence each round start:
  - Redistribute HP so that all allies are raised toward the party's average percentage without exceeding their Max HP (healing only; no ally should lose HP).
  - Grant **Balance tokens** equal to the number of allies healed by the redistribution.
  - When Balance tokens reach **5**, consume them to: 
    - Grant all allies **+50% Crit Rate** and **+50% Mitigation** for 1 turn.
    - Deal **200% Light damage** to the enemy with the highest current HP.
- Token counter persists across turns and resets only when the burst fires.

## Implementation notes
- Implement the plugin under `backend/plugins/cards/`, reusing healing helpers to avoid damage from redistribution and ensuring logs match existing heal events.
- Balance token tracking can live on the party state or card instance; make sure it's accessible in multi-fight runs.
- Confirm Light damage uses the correct damage type hooks so Ryne/LadyLight synergies trigger.
- Update `.codex/implementation/card-inventory.md` and `.codex/planning/archive/726d03ae-card-plan.md` with detailed rules text.
- Extend backend tests covering 5★ cards to verify HP redistribution never harms allies, tokens accumulate correctly, and the burst applies buffs plus targeted damage.

## Deliverables
- Fully realized Equilibrium Prism plugin with stat bonuses, redistribution logic, token tracking, and burst resolution.
- Documentation updates describing the card's mechanics in both reference and planning docs.
- Automated tests ensuring healing math, token cadence, and Light damage bursts behave as expected.

## Player impact
Equilibrium Prism introduces a balance-focused alternative to the existing offensive 5★ lineup, letting Ryne-led parties smooth sustain gaps while unleashing periodic Light detonations that reward careful formation play.
