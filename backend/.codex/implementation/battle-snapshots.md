# Battle snapshots

Battle resolution updates in `game._run_battle` ensure the frontend can safely
poll for results:

- Final snapshots now include an `awaiting_next` flag indicating whether the
  next room can be entered without card or relic choices.
- Reward processing is wrapped in a `try/except`. If an exception occurs, the
  snapshot is populated with any available loot, an `error` message, and
  `awaiting_next` set to `false` so clients are not blocked waiting for results.
- Any exception now yields a snapshot with `result: "error"`, `ended: true`,
  and empty `party` and `foes` arrays so the frontend can detect that combat
  finished even when failures occur.
- The call to `room.resolve` is wrapped in a `try/except` to guard against
  crashes. On failure the battle flag is cleared, map and party data are saved,
  and the snapshot records the `error` with `awaiting_next` set to `false` so
  runs do not hang.
- Snapshots expose active summons through `party_summons` and `foe_summons`.
  Both maps are keyed by the owning combatant's id and store arrays of
  serialized summons. Each summon snapshot also includes an `owner_id` for
  convenience.
- Progress snapshots now include `active_id`, the id of the combatant whose
  action produced the snapshot, so user interfaces can highlight the active
  fighter for both party and foe turns.
- The action queue advances **after** progress snapshots are dispatched so the
  active combatant remains at the head of the queue until user interfaces
  receive and render the update.
- A dedicated `turn_end` handler now advances the queue once damage resolution
  and `turn_end` triggers complete. It emits a final snapshot reflecting the
  updated queue state so clients can accurately track turn progression.

- Foe snapshots include a `rank` field describing encounter difficulty.
  Supported ranks are `"normal"`, `"prime"`, `"glitched prime"`, `"boss"`, and
  `"glitched boss"`.

- Requesting a battle `snapshot` with none available will now start the fight
  using the current room state and return the newly created snapshot instead of
  raising an error.

- If a second battle task is detected during combat, both tasks are cancelled
  and each run receives an error snapshot noting that a concurrent battle was
  detected.

- Repeated calls to `battle_room` while `awaiting_next` is `true` return the
  existing snapshot rather than launching another battle.

These snapshots are stored in `game.battle_snapshots` and polled by the
frontend during combat.

