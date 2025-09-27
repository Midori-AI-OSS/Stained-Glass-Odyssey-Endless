# Party Picker Endpoint

`POST /run/start` accepts a JSON payload with a `party` array of 1–5 owned character IDs (including `player`) and an optional `damage_type` for the player chosen from Light, Dark, Wind, Lightning, Fire, or Ice.
The backend validates the roster, persists the player's damage type, seeds a new map, and returns the run ID, map data, and passive names for each party member.

`POST /ui/action` also exposes an `update_party` action for updating an existing run's roster. The request body should include `{"action": "update_party", "params": {"party": [...]}}` (optionally provide `run_id` inside `params` to target a specific run). The validation rules match `start_run`: the roster must include the `player`, contain 1–5 unique members, exclude `mimic`, and only include characters present in `owned_players`. Successful calls persist the new roster in the `runs` table and return the updated party payload.

## Testing
- `uv run pytest backend/tests/test_party_endpoint.py`
- `uv run pytest backend/tests/test_ui_party_update.py`
