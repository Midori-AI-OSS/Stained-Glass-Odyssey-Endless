# Room Endpoints

The Quart backend exposes routes for core gameplay rooms. Each accepts the
current `run_id` and returns data generated from the plugin system and seeded
maps. Room requests post a JSON body with an optional `action` string, which is
echoed in responses for parity across room types.

## Routes

- `GET /players` – lists all plugin player characters with fields:
  - `id`: plugin identifier
  - `name`: display name
  - `owned`: whether the player owns this character
  - `is_player`: true for the player's avatar
- `POST /run/start` – seeds a `MapGenerator` with the run ID and stores a 10
  node map; responses include the full map and a `current` pointer. Each floor
  guarantees at least one shop.
- `POST /run/<run_id>/next` – advances to the next room after the frontend
  signals that it finished processing the previous one.
- `GET /map/<run_id>` – returns the current map state with fields:
  - `rooms`: upcoming room nodes
  - `current`: index of the next room
  - `battle`: whether a battle is currently running
- `GET /rooms/images` – returns a mapping of room types to background image URLs
  served from `/assets/...`.
- `GET /player/stats` – returns grouped stats and status lists for the player's avatar along with a clamped `refresh_rate` value.
- `GET /assets/<path>` – serves static assets bundled under `backend/assets/`.
- `POST /rooms/<run_id>/battle` – validates the next map node is a battle,
  spawns a random player plugin not in the party as the foe, scales all stats by
  floor, room index, loop, and Pressure, triggers passives, and exchanges attacks
  with the party. The async loop sleeps for 0.002 s between turns. Responses include
  full stats for both sides plus up to three unused `card_choices` of the appropriate
  star rank and the party's full `cards` list. See `battle-endpoint-payload.md` for
  payload details. The map pointer is not advanced until the client calls
  `POST /run/<run_id>/next` (after any card selection).
- `POST /rooms/<run_id>/shop` – validates the next node is a shop, heals the
  party by 5% of its total max HP, deducts the provided `cost` from the shared
  gold pool, and appends any purchased `item` to a shared relic list. The request
  accepts `{ "action": "" }` and responses include updated `gold`, `relics`, and
  `cards` values. On success the server marks the run as ready to advance and
  includes `next_room` in the response; the pointer advances when the client
  calls `POST /run/<run_id>/next`.
- `POST /rooms/<run_id>/boss` – validates the next node is a `battle-boss-floor`
  room and runs a high-powered battle. The request accepts `{ "action": "" }`
  and responses mirror normal battles but scale foe stats heavily and offer
  higher-star `card_choices` when available. The map pointer advances only after
  `POST /run/<run_id>/next`.
- `POST /cards/<run_id>` – accepts a chosen `card` ID from the latest battle and
  adds it to the party if unowned, returning the updated `cards` list.
- `POST /rooms/<run_id>/<room_id>/action` – generic handler for unimplemented room
  types; echoes the provided `action` string (defaulting to `"noop"`) alongside
  `run_id` and `room_id`.

All routes read and write state through `SaveManager`, which uses `AF_DB_PATH`
and a key from `AF_DB_KEY` or `AF_DB_PASSWORD`. Party data stored per run
includes member IDs, shared gold, and relics.

## Testing
- `uv run pytest backend/tests/test_app.py::test_players_and_rooms`
- `uv run pytest backend/tests/test_app.py::test_room_images`
- `uv run pytest backend/tests/test_mapgen.py::test_generator_deterministic`
- `uv run pytest backend/tests/test_passives.py`
- `uv run pytest backend/tests/test_room_action.py::test_room_action_echoes_request`
