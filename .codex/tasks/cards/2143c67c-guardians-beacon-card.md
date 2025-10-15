# Add 2★ card: Guardian's Beacon inspired by Carly

## Summary
Introduce a defensive two-star card that channels Carly's protective playstyle by blending large defense scaling with targeted sustain. The goal is to support defensive or sustain-heavy parties without duplicating Iron Guard.

## Design requirements
- Name the card **Guardian's Beacon** and register it as a 2★ reward.
- Baseline stats: **+55% DEF** to align with other defensive 2★ options.
- Passive effect: at the end of each turn, heal the lowest-HP ally for **8% of their Max HP**. If that ally's damage type is **Light**, also grant them **+10% Mitigation for 1 turn**.
- Healing should respect overheal rules and mitigation stacks should expire normally at turn end.

## Implementation notes
- Implement the new plugin in `backend/plugins/cards/`, wiring into the turn-end hooks that existing sustain cards use.
- Ensure the Light element check leverages the same damage-type metadata covered in `.codex/implementation/player-foe-reference.md`.
- Update `.codex/implementation/card-inventory.md` and `.codex/planning/archive/726d03ae-card-plan.md` to list the new reward under 2★ cards with its full effect text.
- Add or extend backend tests validating 2★ card registration and the healing/mitigation trigger (mocking a Light ally to confirm the conditional bonus).

## Deliverables
- Card plugin with metadata, star rank, stat bonuses, and passive trigger logic.
- Documentation updates reflecting the new card in both reference and planning files.
- Automated test coverage proving the end-of-turn heal and Light-aligned mitigation bonus work as specified.

## Player impact
Guardian's Beacon provides a fresh sustain option for defensive squads, letting Carly-focused teams or Light-heavy parties maintain shields without relying solely on revival-centric cards.
