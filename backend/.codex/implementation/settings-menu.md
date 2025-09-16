# Settings Menu Backend Integration

## Turn Pacing Option
- The `turn_pacing` option is stored in the `options` table via `options.OptionKey.TURN_PACING`.
- `autofighter.rooms.battle.pacing` loads the persisted value during module import with `get_option(OptionKey.TURN_PACING, 0.5)`.
- `set_turn_pacing()` clamps the pacing value to a positive number (minimum `0.05` seconds) and refreshes derived delays (`YIELD_DELAY`, `DOUBLE_YIELD_DELAY`) and multipliers used by the pacing helpers.
- `refresh_turn_pacing()` rereads the option from storage so other services can rehydrate the runtime pacing value without restarting the backend.

## API Endpoints
- `GET /config/turn-pacing`
  - Returns the current pacing (`turn_pacing`) and the default of `0.5` seconds.
  - Refreshes the in-memory pacing constant so the backend reflects any out-of-band changes to the option.
- `POST /config/turn-pacing`
  - Accepts a JSON body with a positive `turn_pacing` value (seconds between actions).
  - Persists the sanitized value via `options.set_option` and calls `pacing.set_turn_pacing` so the running battle loop immediately adopts the new cadence.
  - Responds with the applied pacing and the default for UI slider calibration.

## Combat Flow Impact
- `TURN_PACING` is the base delay applied by `pace_sleep()` between player and foe actions.
- Lower values produce faster combat animations and shorter waits between queued actions; higher values give the UI more time to animate each step.
- Because `YIELD_DELAY` scales with the pacing value, cooperative waits during heavy load stay proportional to the configured cadence.
