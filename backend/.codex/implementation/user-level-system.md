# User level system

Tracks a global user level and experience stored in the options table.

* `user_level_service.py` persists `user_level` and `user_exp`.
* `gain_user_exp(amount)` asynchronously adds experience and handles level
  ups using a 1.05× growth curve defined by `user_exp_to_level()`. Writes are
  offloaded to a worker thread so battle resolution does not block the event
  loop.
* Battle rewards divide experience by the current user level. Party members
  gain the full amount, then the scaled value is credited to the user through
  `gain_user_exp()` so character rewards remain unaffected.
* A status hook applies a 1 % per-level multiplier to all party stats at runtime.
* Player endpoints expose `{level, exp, next_level_exp}` so the frontend can
  render progress.
