# Turn Loop Package

The battle turn loop now lives in a dedicated package at
`backend/autofighter/rooms/battle/turn_loop/`. The module breakup keeps the
primary `run_turn_loop()` orchestrator small and focused on coordinating helper
modules:

- `initialization.py` builds a `TurnLoopContext`, primes action points for all
  participants, and emits the initial progress update before the battle loop
  begins. After dispatching the first snapshot it now consults
  `_intro_pause_seconds` to decide whether to briefly hold the intro banner for
  the UI. The delay scales from 0.75s up to 1.75s based on the number of visible
  combatants and is skipped entirely when no visual queue is active so fast
  battles are not artificially throttled.
- `player_turn.py` processes the party phase, including enrage updates, damage
  resolution, summon management, and progress/visual updates. The helper mutates
  the shared context with revised turn counts, rewards, and pacing data.
- `foe_turn.py` mirrors the party phase for foes, handling targeting, effect
  ticks, ultimates, and post-action bookkeeping for enemy actors.
- `cleanup.py` centralizes shared predicates ("are foes still alive?"), and
  performs the `remove_dead_foes()` sweep that previously lived at the bottom of
  the monolithic loop.
- `turn_end.py` hosts `finish_turn()`, the shared helper that applies pacing,
  pushes progress updates, and dispatches the final turn snapshot for both
  player and foe actors.
- `orchestrator.py` hosts the thin `run_turn_loop()` function. It delegates to
  the helpers above, re-checks battle state between phases, and returns the final
  `(turn, temp_rdr, exp_reward)` tuple.

`TurnLoopContext` is the glue structure shared across helpers. It keeps mutable
lists (foes, effect managers, enrage modifiers) and dynamic counters (current
turn, temporary RDR, experience reward, credited foes) together with external
collaborators such as the registry callbacks and battle task manager. All helper
functions operate on this context so that state changes in one phase are
immediately visible to the others.
