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
- Document the card in `.codex/implementation/card-inventory.md` and update the planning entry in `.codex/planning/archive/726d03ae-card-plan.md`.
- Extend backend tests for 3★ card registration and add targeted unit coverage to confirm the Flux counter, damage burst, and resistance buff fire at exactly five debuff applications.

## Deliverables
- Fully implemented card plugin with stat bonuses, Flux counter tracking, AoE damage trigger, and resistance buff handling.
- Updated docs listing Flux Convergence with accurate rules text.
- Passing backend tests covering registration and the Flux mechanic edge cases.

## Player impact
Flux Convergence gives debuff-centric teams—especially those fielding Kboshi or LadyDarkness—a reason to invest in multi-turn control loops, providing reliable AoE bursts and protection against incoming cleanses.

---

## Audit notes (2025-02-18)

- ❌ Stat debuff tracking fails because `StatModifier` instances produced by `create_stat_buff` have no `source` attribute; `_on_effect_applied` exits early when `source not in party.members`, so flux never increments for standard defense/mitigation debuffs despite the specification calling them out.【F:backend/plugins/cards/flux_convergence.py†L74-L87】【F:backend/autofighter/effects.py†L101-L140】
- ❌ The automated regression suite does not pass—`uv run pytest tests/test_flux_convergence.py` reports two failing cases (`burst_at_five` never damages stored foes and the counter over-increments). The failures block CI and indicate the feature was not validated as claimed.【48f40a†L1-L44】
- ⚠️ The planning archive in `.codex/planning/archive/726d03ae-card-plan.md` still lacks a Flux Convergence entry under the 3★ section, so documentation is incomplete.【F:.codex/planning/archive/726d03ae-card-plan.md†L40-L64】

more work needed — card does not yet meet the acceptance criteria above; please address the failing tests and stat-debuff detection before resubmitting.
