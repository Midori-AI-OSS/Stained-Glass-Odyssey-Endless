# Audit: Completed Task Review

## Scope
- `.codex/tasks/cards/d66727fc-farsight-scope-before-attack.md`
- `.codex/tasks/passives/a2c66553-lady-echo-hit-tracking.md`
- Backend combat flow (`backend/autofighter/stats.py`, `backend/autofighter/passives.py`)
- Related plugins and tests (`backend/plugins/cards/farsight_scope.py`, `backend/plugins/passives/normal/lady_echo_resonant_static.py`,
  `backend/tests/test_farsight_scope.py`, `backend/tests/test_lady_echo_resonant_static.py`)
- Documentation updates in `.codex/implementation/event-bus.md`

## Findings

### Farsight Scope trigger audit
- ✅ **Before-attack hook now exists in live combat.** `Stats.apply_damage` emits the `before_attack` event immediately before dodge rolls,
  propagating staged attack metadata so plugins can react in real battles.【F:backend/autofighter/stats.py†L760-L820】
- ✅ **Card listener correctly applies and cleans up the crit buff.** The plugin wires to `before_attack`, spawns an effect manager on demand,
  applies a one-turn +6% crit modifier when the target is <50% HP, and removes it on `action_used` to prevent leaks.【F:backend/plugins/cards/farsight_scope.py†L1-L71】
- ✅ **Regression coverage hits real combat flow.** New tests assert the buff applies when the bus event fires directly and when `apply_damage`
  runs inside a battle, including cleanup after `action_used`.【F:backend/tests/test_farsight_scope.py†L1-L58】
- ✅ **Docs mention the new event.** Event bus documentation lists `before_attack` with metadata semantics so other teams can integrate.【F:.codex/implementation/event-bus.md†L52-L64】
- ⚠️ **Note:** The handler re-subscribes to `action_used` on every trigger. Because the cleanup unsubscribes itself, no residual listeners remain,
  but we should keep an eye on multi-hit actions for duplicate removals (no issue observed in tests).

### Lady Echo Resonant Static audit
- ✅ **Passive listens to the correct hook.** `trigger="hit_landed"` combined with `on_hit_landed` ensures the consecutive-hit logic executes when
  real attacks land, matching the PassiveRegistry contract.【F:backend/plugins/passives/normal/lady_echo_resonant_static.py†L12-L118】【F:backend/autofighter/passives.py†L184-L213】
- ✅ **Chain damage and crit stacks behave as intended.** The passive now tracks per-target combos, resets when targets change, and applies
  party crit effects using the Stats effect API.【F:backend/plugins/passives/normal/lady_echo_resonant_static.py†L60-L104】
- ✅ **Automated coverage added.** Tests cover DoT counting via effect manager vs. fallback lists, consecutive-hit stacking, and reset behavior.
  All pass under `uv run pytest` in strict asyncio mode.【F:backend/tests/test_lady_echo_resonant_static.py†L1-L113】【0b55f9†L1-L11】

## Verdict
Both “ready for review” tasks meet their acceptance criteria, have regression coverage, and include relevant documentation updates. No blockers found.
