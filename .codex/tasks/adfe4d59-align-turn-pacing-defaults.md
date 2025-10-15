# Harmonize turn pacing defaults and intro delay

## Summary
The backend uses a 0.2 s `TURN_PACING` while the config route and Settings UI assume 0.5 s. Combined with a hardcoded `pace_sleep(3 / TURN_PACING)` call, battle intros stall for 15 s by default (and even longer when pacing is lowered). We should align defaults and make the intro pause conditional.

## Details
* The pacing helper sets `DEFAULT_TURN_PACING = 0.2`, but API consumers expose a 0.5 default, so refreshing options snaps to different baselines depending on caller.【F:backend/autofighter/rooms/battle/pacing.py†L16-L57】【F:backend/routes/config.py†L16-L108】【F:frontend/src/lib/components/SettingsMenu.svelte†L25-L118】
* Turn-loop initialization sleeps for `3 / TURN_PACING` after the first progress update, which is 15 s at the 0.2 backend default and scales inversely with faster pacing (e.g., 30 s if a player dials pacing to 0.1).【F:backend/autofighter/rooms/battle/turn_loop/initialization.py†L139-L153】

## Requirements
- Decide on a single canonical default pacing value (with product input) and update backend constants, API payloads, and the Settings UI to match.
- Replace the fixed `3 / TURN_PACING` pause with a smarter gating mechanism (e.g., skip when no cinematic/intro assets exist, or cap the wait to a small constant).
- Add regression coverage that the `/config/turn_pacing` endpoint and frontend slider display the same default, and document the intro pacing behavior.
- Verify that existing options migrations/tests still pass with the new default.

ready for review
