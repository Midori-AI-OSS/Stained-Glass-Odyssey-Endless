# Map Generator

`MapGenerator` builds deterministic 10-room floors from a seed. Each floor
contains:

- 1 shop
- battles marked as `battle-weak` or `battle-normal`
- a final `battle-boss-floor`

Rooms are stored as `MapNode` entries with fields:

- `room_id`: unique index within the floor
- `room_type`: `start`, `battle-weak`, `battle-normal`, `shop`, or `battle-boss-floor`
- `floor`, `index`, `loop`, `pressure`

Run IDs seed generation so repeated runs produce identical layouts, but a seed
may not be reused for another run. Chat rooms may appear after battles only when
LLM extras are installed and never more than six times per floor. These rooms do
not consume room slots. The Quart backend serializes nodes to JSON and advances a
`current` pointer as endpoints resolve rooms.

Stats and rewards scale by multiplying base values with `floor × index × loop × (1 + 0.05 × pressure)`.
