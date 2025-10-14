# Make Guiding Compass bonus truly run-limited

## Summary
Guiding Compass is intended to grant a one-time XP bonus on the first battle of a run, but its current implementation triggers every battle because the "used" flag resets on each battle end and the card instance is recreated per fight.

## Details
* `GuidingCompass.apply()` tracks `first_battle_bonus_used` inside the card instance and clears it on `battle_end`.【F:backend/plugins/cards/guiding_compass.py†L19-L55】
* Cards are re-instantiated whenever `apply_cards()` runs for a new combat, so the local boolean resets to `False` before every battle even without the explicit reset.
* As a result, every battle grants the "first battle" bonus, inflating XP gains.

## Requirements
- Persist a per-run flag (e.g., on the party or run state) so the bonus fires only once per run.
- Ensure multiple party members with the card don't double-award the bonus.
- Add regression coverage proving the bonus does **not** trigger on the second battle of the same run but does on a brand new run.
- Update any relevant documentation that mentions the Guiding Compass bonus behavior.
ready for review
