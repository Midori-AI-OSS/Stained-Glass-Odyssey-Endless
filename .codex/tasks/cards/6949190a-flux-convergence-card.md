# Add 3★ card: Flux Convergence honoring Kboshi

## Summary
Deliver a high-impact three-star reward that channels Kboshi's flux manipulation by rewarding debuff-centric teams. The design should lean into dark-element control without duplicating existing crit engines.

## Design requirements
- Name the card **Flux Convergence** and designate it as a 3★ reward.
- Base stats: **+255% Effect Hit Rate** to help status-heavy squads stick their debuffs.
- Passive loop:
  - Track a global **Flux counter** that increments each time any ally successfully applies a debuff to an enemy.
  - When the counter reaches **5 stacks**, immediately consume all stacks to deal **120% ATK dark damage** to all foes and grant the debuffing ally **+20% Effect Resistance for 1 turn**.
  - Flux counter should persist across turns but reset whenever it triggers, encouraging steady debuff application.
- Damage instance should leverage the existing dark damage type hooks so related passives can react.

## Implementation notes
- Implement the plugin under `backend/plugins/cards/`, using shared event hooks for debuff application (consult `.codex/implementation/stats-and-effects.md` for debuff plumbing).
- Ensure AoE damage respects mitigation and logs correctly through the damage manager.
- Document the card in `.codex/implementation/card-inventory.md`.
- Extend backend tests for 3★ card registration and add targeted unit coverage to confirm the Flux counter, damage burst, and resistance buff fire at exactly five debuff applications.

## Deliverables
- Fully implemented card plugin with stat bonuses, Flux counter tracking, AoE damage trigger, and resistance buff handling.
- Updated docs listing Flux Convergence with accurate rules text.
- Passing backend tests covering registration and the Flux mechanic edge cases.

## Player impact
Flux Convergence gives debuff-centric teams—especially those fielding Kboshi or LadyDarkness—a reason to invest in multi-turn control loops, providing reliable AoE bursts and protection against incoming cleanses.

## Audit (2025-02-24)

- ✅ Validated the Flux counter workflow and burst execution in `FluxConvergence`, including foe tracking, debuff source attribution, dark-damage swapping, and resistance buff cleanup; multiplicative stat buff setup matches 3★ baselines.【F:backend/plugins/cards/flux_convergence.py†L1-L208】
- ✅ Ran `uv run pytest tests/test_flux_convergence.py` to cover stat bonuses, counter increments, burst triggering at exactly five debuffs, resistance buff application, and counter reset behaviour (all passing).【2481e6†L1-L5】
- ✅ Confirmed documentation alignment in `.codex/implementation/card-inventory.md`, ensuring the 3★ roster describes Flux Convergence with the implemented burst and resistance loop.【F:.codex/implementation/card-inventory.md†L33-L50】

requesting review from the Task Master
