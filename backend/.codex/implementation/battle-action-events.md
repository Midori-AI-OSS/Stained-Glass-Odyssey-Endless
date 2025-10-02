# Battle action events

The battle system emits additional events to coordinate turn-based effects and
passive abilities:

- `action_used` – emitted from `rooms/battle/core.py` whenever a combatant completes
  an action.  Subscribers receive the acting entity, the target, and the amount
  of damage or healing dealt.
- `extra_turn` – grants an immediate extra action to the recipient.  The battle
  loop tracks pending turns so effects like **SwiftFootwork** or **EchoBell** can
  schedule additional moves without creating infinite loops.
- `summon_created` – emitted when a summon enters play.
- `summon_removed` – emitted when a summon leaves play for any reason.
- `summon_defeated` – emitted after a summon is killed and removed, allowing
  passives like **Menagerie Bond** to respond.
- `target_acquired` – dispatched immediately after a combatant selects a
  target. The acting entity and chosen target are provided so clients can
  highlight the intended victim before damage resolves.
- `dodge` – dispatched from `Stats.apply_damage` when an incoming attack is
  avoided. Subscribers receive the dodging entity, the attacker (or `None` if
  environmental), the raw damage amount that would have been applied, the
  resolved action name, and a metadata dictionary containing the dodger and
  attacker ids along with the emitting source (`{"source": "stats.apply_damage"}`).

Damage type ultimates are invoked directly from `rooms/battle/core.py` when
`ultimate_ready` is set. Each damage type plugin is responsible for consuming
charge through its own `use_ultimate()` call and may add additional effects in
its `ultimate` method or respond to the `ultimate_used` event.

## Pacing

Each action calls the `_pace` helper in `rooms/battle/pacing.py`, which yields for roughly half a
second based on the time spent executing the move. After `_turn_end` resolves,
the loop now pauses an additional **2.2 seconds** before advancing to the next
actor so turn-end events can finish processing. This per-actor pacing keeps
combat readable while avoiding full-turn delays.
