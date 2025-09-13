# SaveManager

Wrapper around SQLCipher connections and database migrations with enhanced security.

Use `get_save_manager()` from `game.py` to obtain an initialized instance. The
function lazily constructs the manager, runs migrations, and performs initial
setup so tests can override `AF_DB_PATH` and `AF_DB_KEY` before the first call.

## Security Features

The SaveManager implements comprehensive security measures to protect encrypted data:

- **Strong Key Derivation**: PBKDF2 with SHA-256, 100,000 iterations, and 256-bit salt
- **SQL Injection Prevention**: Proper quote escaping and input validation
- **No Silent Fallbacks**: Hard failures when encryption is not available
- **Secure File Permissions**: Database files restricted to owner read/write only
- **Comprehensive Audit Logging**: Security events logged for monitoring
- **Defense in Depth**: Multiple overlapping security controls

See [save-manager-security.md](save-manager-security.md) for detailed security documentation.

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

## Run snapshots
- `POST /run/start` clones the player's pronouns, damage type, and stat points
  into the run record so mid-run edits to the player editor do not change the
  active party.
- `save_party` persists the player's current damage type and stat allocations so
  customized values remain applied when loading subsequent rooms.
