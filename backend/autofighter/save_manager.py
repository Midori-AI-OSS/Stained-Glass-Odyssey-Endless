from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sys
import re

# Handle platform-specific SQLite encryption imports
if sys.platform == 'win32':
    try:
        import pysqlcipher3.dbapi2 as sqlcipher3
    except ImportError:
        # Fallback to regular sqlite3 on Windows if pysqlcipher3 fails
        import sqlite3 as sqlcipher3
        sqlcipher3.set_key = lambda conn, key: None  # No-op for fallback
else:
    import sqlcipher3


class SaveManager:
    """Wrapper around SQLCipher connections.

    Keys are read from ``AF_DB_KEY`` or derived from ``AF_DB_PASSWORD``.
    """

    def __init__(self, db_path: Path, key: str) -> None:
        self.db_path = Path(db_path)
        self.key = key

    @classmethod
    def from_env(cls) -> SaveManager:
        db_path = Path(
            os.getenv("AF_DB_PATH", Path(__file__).resolve().parent.parent / "save.db")
        )
        key = os.getenv("AF_DB_KEY")
        password = os.getenv("AF_DB_PASSWORD")
        if not key and password:
            key = hashlib.sha256(password.encode()).hexdigest()
        return cls(db_path, key or "")

    @contextmanager
    def connection(self) -> Iterator[sqlcipher3.Connection]:
        conn = sqlcipher3.connect(self.db_path)
        if self.key:
            try:
                if hasattr(conn, "set_key"):
                    conn.set_key(self.key)
                else:
                    conn.execute("PRAGMA key = ?", (self.key,))
            except Exception:
                # Some drivers (notably Windows builds) do not support parameter
                # substitution for the PRAGMA statement. For maximal security, do not attempt string interpolation.
                conn.close()
                raise RuntimeError(
                    "Your SQLCipher driver does not support parameter substitution for PRAGMA key. "
                    "For security reasons, direct string substitution is not allowed. "
                    "Please use a supported driver/version or platform."
                )
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def migrate(self, migrations_dir: Path) -> None:
        migrations = sorted(migrations_dir.glob("*.sql"))
        with self.connection() as conn:
            current = conn.execute("PRAGMA user_version").fetchone()[0]
            for path in migrations:
                version_part = path.stem.split("_")[0]
                if not version_part.isdigit():
                    # Skip files that don't begin with a numeric prefix. This ensures
                    # we never execute a script whose version component could inject
                    # arbitrary SQL when setting ``PRAGMA user_version``.
                    continue
                version = int(version_part)
                if version <= current:
                    continue
                conn.executescript(path.read_text())
                # ``PRAGMA user_version`` doesn't support parameter substitution.
                # ``version`` is sanitized above, so this f-string remains safe.
                conn.execute(f"PRAGMA user_version = {version}")
