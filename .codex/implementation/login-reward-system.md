# Daily Login Reward System

The daily login reward system grants players a bundle of damage-type upgrade
items for logging in and actively clearing rooms each day.

## Reset Window
- Rewards operate on a Pacific Time (PT) schedule.
- Each reward day begins at **2:00 AM PT** and ends at the next 2:00 AM PT.
- Logging in after the window elapses resets the streak to 1.

## Streak Tracking
- Streak metadata is stored in the encrypted `options` table under the
  `login_rewards` key.
- Stored fields:
  - `streak`: current consecutive day count.
  - `last_login_day` / `last_login_at`: most recent reward day and timestamp.
  - `last_claim_day` / `last_claim_at`: claim information for the active day.
  - `rooms_day`: reward day associated with the recorded room clears.
  - `rooms_completed`: cleared room count for the active day.
- Any state decoded from `login_rewards` is sanitized before use. Missing or
  malformed data automatically reverts to default values.

## Room Completion Requirement
- Players must clear **three rooms** within the active reward window before the
  daily bundle is granted.
- Every successful room advancement triggers `record_room_completion`, which:
  - Refreshes the reward-day bookkeeping.
  - Increments the running room counter for the day.
  - Automatically grants the daily bundle as soon as the requirement is met,
    provided the day has not already been fulfilled.
- Room clears from previous reward days do not carry forward.

## Reward Calculation
- Baseline reward: **1× random 1★** damage-type upgrade item per day.
- Bonus scaling:
  - +1 additional 1★ item for every 7 days in the streak (`⌊streak / 7⌋`).
  - +1 additional 2★ item for every 100 days in the streak (`⌊streak / 100⌋`).
- Items are selected from the same Lucent damage-type pool used by battle loot.
- Reward bundles are generated once per PT reward day and cached so repeated
  status checks surface the identical preview until the next 2 AM reset.
- Each reward entry contains an `item_id` (e.g., `fire_1`), the lowercase
  `damage_type`, the `stars` value, and a friendly `name` string for UI
  display.
- Claimed rewards are merged into the `upgrade_items` inventory with the normal
  `GachaManager` auto-crafting pass.

## API Endpoints
- `GET /rewards/login`
  - Refreshes the login streak for the current PT window.
  - Returns streak length, room progress, claim availability, and a preview of
    the day's reward bundle.
- `POST /rewards/login/claim`
  - Fallback endpoint that attempts to grant the bundle if the automatic flow
    has not yet fulfilled the day.
  - Returns an error when the requirement is unmet or when the daily bundle has
    already been delivered by the auto-claim logic.
- Responses include `seconds_until_reset` and the ISO timestamp of the next
  2:00 AM PT reset to aid frontend countdown timers.

## Failure Modes
- Claim attempts before clearing three rooms produce `400` responses with the
  `daily requirement not met` error message.
- Requests after the automatic grant has already run return `400` responses with
  `reward already claimed`.
- Database read or write issues are isolated so that room advancement continues
  even if the reward bookkeeping encounters an error; the failure is logged and
  retried on the next interaction.

## Frontend Panel
- `LoginRewardsPanel.svelte` renders the centered main-menu banner and refreshes
  `/rewards/login` on mount, tab focus, manual refresh, and while waiting for an
  auto-claim to complete.
- The panel shows up to the most recent 12 streak days using chevron badges,
  truncating with a leading ellipsis when streaks exceed the window.
- Countdown ticks locally from the `seconds_until_reset` field; hitting zero
  schedules an automatic refresh to pick up the next day's bundle.
- Reward previews enumerate item names, star ratings, and damage types; status
  messaging communicates whether the day's bundle has already been delivered.

## Visual Reference
- Refer to `.codex/docs/login-rewards-panel.svg` for an annotated layout of the
  main menu banner, including streak chevrons, countdown, room progress, and the
  claim action states.
