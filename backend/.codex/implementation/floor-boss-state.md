# Floor Boss State Snapshot

`services/run_service.start_run` and `services.room_service.boss_room` persist
the currently active boss encounter on the run state under the
`floor_boss` key. The snapshot is used when resuming a floor or re-entering a
boss room so the backend can restore the same foe without rerolling.

The record now includes positional metadata so boss rush encounters can be
distinguished even when they share the same floor/loop identifiers:

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Plugin identifier for the foe selected for the boss room. |
| `floor` | `int` | Floor number the boss was generated for. |
| `loop` | `int` | Loop counter for ascension-style replays of the same floor. |
| `index` | `int` | Zero-based room index from `MapGenerator`. Present when the
  source node exposes an `index` or `room_id` attribute. |
| `room_id` | `int` | Persistent room identifier mirrored from the map node when
  available. Used as a fallback when the generator does not expose a stable
  index. |

When resuming a run the boss room loader verifies that `id`, `floor`, `loop`,
`index`, and `room_id` match the current node. If any of these fields differ
the snapshot is discarded and a new boss is rolled for the encounter. This keeps
restart behaviour unchanged for standard floors while guaranteeing that boss
rush nodes roll unique foes on each visit.
