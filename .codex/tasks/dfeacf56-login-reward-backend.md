Coder, implement a backend system to grant daily login rewards that scale with consecutive play.

## Requirements
- Track per-account login streaks and last login timestamps.
- Reset streak at 2am Pacific Time if the user misses a day.
- Daily reward becomes available after the player completes 3 rooms in a calendar day.
- Base reward: 1 random 1★ damage-type item each day.
- Every 7-day streak adds +1 additional random 1★ damage-type item.
- Every 100-day streak adds +1 random 2★ damage-type item to the daily reward.
- Support duplicated items; no uniqueness enforcement.
- Persist streak data in the existing player profile storage.

## Notes
- Ensure time zone handling uses PT regardless of server location.
- Provide clear hooks to expose reward data via API.

task ready for review
