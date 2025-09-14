Coder, implement a dedicated encrypted tracking database to record every run, menu interaction, and party action for analytics.

## Requirements
- Create a separate SQLCipher-encrypted SQLite database (`track.db`) managed by a new `TrackingDBManager`.
- Derive the encryption key using the same mechanism as `SaveManager` (env-based password or key).
- Define normalized schema:
  - `runs(run_id TEXT PRIMARY KEY, start_ts INT, end_ts INT, outcome TEXT)`
  - `party_members(run_id TEXT, slot INT, character_id TEXT, stats_json TEXT)`
  - `cards(run_id TEXT, room_id TEXT, card_id TEXT)`
  - `relics(run_id TEXT, room_id TEXT, relic_id TEXT)`
  - `battle_summaries(run_id TEXT, room_id TEXT, turns INT, dmg_dealt INT, dmg_taken INT, victory INT)`
  - `character_pulls(pull_id TEXT PRIMARY KEY, ts INT, character_id TEXT, rarity TEXT, source TEXT)`
  - `menu_actions(action_id TEXT PRIMARY KEY, ts INT, menu_item TEXT, result TEXT, details_json TEXT)` – record each selection from the main menu (`Run`, `Party`, `Warp`, `Inventory`, `Guidebook`, `Settings`, `Feedback`) and any follow-on context.
  - `game_actions(run_id TEXT, room_id TEXT, action_type TEXT, details_json TEXT)`
  - `settings_changes(action_id TEXT PRIMARY KEY, ts INT, setting TEXT, old_value TEXT, new_value TEXT)`
  - `deck_changes(run_id TEXT, room_id TEXT, change_type TEXT, card_id TEXT, details_json TEXT)` – upgrades, removals, transforms, duplications.
  - `shop_transactions(run_id TEXT, room_id TEXT, item_type TEXT, item_id TEXT, cost INT, action TEXT)`
  - `event_choices(run_id TEXT, room_id TEXT, event_name TEXT, choice TEXT, outcome_json TEXT)`
  - `overlay_actions(action_id TEXT PRIMARY KEY, ts INT, overlay TEXT, details_json TEXT)` – openings of Inventory, Guidebook, Settings, etc.
  - `play_sessions(session_id TEXT PRIMARY KEY, user_id TEXT, login_ts INT, logout_ts INT, duration INT)` – aggregate playtime per login session.
  - `login_events(event_id TEXT PRIMARY KEY, ts INT, user_id TEXT, method TEXT, success INT, details_json TEXT)` – track authentication attempts for future login systems.
  - `achievement_unlocks(run_id TEXT, achievement_id TEXT, ts INT, details_json TEXT)`
- Hook into game flow to write entries:
  - Run start/end events.
  - Party composition and member stats upon run start.
  - Each card or relic acquisition with room reference.
  - Summary data after each battle (no full logs).
  - Character pulls/gacha events.
  - Main menu navigation for every item (`Run`, `Party`, `Warp`, `Inventory`, `Guidebook`, `Settings`, `Feedback`), including cancelations or disabled selections.
  - Major gameplay actions such as shop purchases, upgrades, event choices, potion uses, deck edits, map selections, settings changes, overlay openings, run aborts/restarts, time spent in menus, login/logout events, and total playtime per session.
- Ensure writes are batched/asynchronous to avoid performance hits.
- Provide migration/initialization script for the new database file.
- Expose read-only API endpoints to retrieve run histories and aggregates for future tracking features.
- Update `.codex/implementation/save-system.md` (or add a new doc) to describe the tracking database architecture and schema.

## Notes
- Do not store detailed battle logs or per-turn actions—only aggregate metrics.
- Maintain separation from the primary save database to avoid corrupting player saves.
- Schema should be extensible for future action types and analytics.
