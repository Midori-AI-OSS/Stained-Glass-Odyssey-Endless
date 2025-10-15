# Encrypted Save System

## Setup
- Uses [SQLCipher](https://www.zetetic.net/sqlcipher/) via the `sqlcipher3-binary` package.
- `SaveManager` reads `AF_DB_PATH` for the database location (defaults to `save.db` in the repository root) and derives a key
  from either `AF_DB_KEY` or `AF_DB_PASSWORD`.
- Install dependencies with `uv add sqlcipher3-binary`.

## Schema
- `runs(id TEXT PRIMARY KEY, party TEXT, map TEXT)` stores the current run state. The `map` JSON now always contains a `reward_staging` object with `cards`, `relics`, and `items` arrays so staged rewards persist across reconnects without mutating the `party` payload.
- `options(key TEXT PRIMARY KEY, value TEXT)` stores player customization and settings.
- Additional tables for players and settings will be added as features return.

## Player Customization Storage
Player customization values are stored in the `options` table under the `player_stats` key as JSON:
```json
{"hp": 20, "attack": 30, "defense": 50}
```

These values are applied directly to base stats during player instantiation rather than as temporary modifiers, ensuring consistent stats across save/load cycles and preventing exponential growth bugs.

## Usage
```python
from autofighter.save_manager import SaveManager

mgr = SaveManager.from_env()
mgr.migrate(Path("backend/migrations"))
with mgr.connection() as conn:
    conn.execute("INSERT INTO runs (id, party, map) VALUES ('1', '[]', '[]')")
```
All database access flows through `SaveManager`, which batches writes and
handles key setup.

## Recovery
- Supply the same key material or password to reopen the database.
- Back up both the encrypted `save.db` and any stored key material to prevent
  data loss. Migration scripts under `backend/migrations/` keep schemas forward
  compatible.
