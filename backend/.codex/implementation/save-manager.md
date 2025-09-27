# SaveManager

Wrapper around SQLCipher connections and database migrations.

Use `get_save_manager()` from `game.py` to obtain an initialized instance. The
function lazily constructs the manager, runs migrations, and performs initial
setup so tests can override `AF_DB_PATH` and `AF_DB_KEY` before the first call.

## Migration safety
- Migration filenames must start with a numeric prefix (`NNN_description.sql`).
- Non-numeric prefixes are ignored to prevent executing unexpected scripts.
- `PRAGMA user_version` does not accept parameter binding; the version value is
  cast to `int` before being interpolated to avoid SQL injection.

## Backup and restore
- `GET /save/backup` exports the `runs`, `options`, and `damage_types` tables
  as JSON, hashes the plaintext payload with SHA-256, embeds the hash, then
  encrypts the package with Fernet using a key derived from the database key.
- `POST /save/restore` accepts the encrypted blob, decrypts and verifies the
  embedded hash, and repopulates the tables only if the digest matches.
- `POST /save/wipe` deletes the encrypted database file and reruns migrations,
  recreating `runs`, `owned_players`, `options`, and `damage_types`. A random
  starting persona (either LadyDarkness or LadyLight) is inserted into
  `owned_players` after migrations. Any new tables must have corresponding
  migrations so wipes rebuild them.
  `DELETE /run/<id>` removes a single active run without touching other data.

## Tracking database
- Telemetry lives in a separate SQLCipher database (`track.db`) managed by
  `tracking.TrackingDBManager`. The encryption key is derived from the same
  environment variables as the primary save database (`AF_DB_KEY` or the SHA-256
  of `AF_DB_PASSWORD`).
- `tracking/migrations` bootstrap the schema, which records run metadata,
  battle summaries, menu interactions, deck changes, shop transactions, overlay
  usage, gacha pulls, login events, and play session durations. Battle summary
  rows include a `logs_url` pointer so downstream analytics can reference the
  `/logs/<run_id>/battles/<index>` endpoints rather than storing duplicate
  combat payloads.
- Migration `002_add_logs_url_to_battle_summaries.sql` backfills the pointer on
  existing telemetry databases and automatically skips if the column already
  exists so fresh installs do not error when updating to the new schema.
- `tracking.service` exposes async helpers (e.g., `log_run_start`,
  `log_battle_summary`, `log_menu_action`) that offload writes to background
  threads so gameplay coroutines remain responsive.
- Read-only analytics endpoints are available under `/tracking/*` for run lists,
  run detail breakdowns, and aggregate statistics. The main `app.py`
  registers the blueprint automatically.
- Runs, sessions, and defeat events synchronise both databases: defeating a run
  updates the telemetry tables before the encrypted save record is deleted, and
  manual run ends update telemetry through the UI routes.

## Run snapshots
- `POST /run/start` clones the player's pronouns, damage type, and stat points
  into the run record so mid-run edits to the player editor do not change the
  active party.
- `save_party` persists the player's current damage type and stat allocations so
  customized values remain applied when loading subsequent rooms.
