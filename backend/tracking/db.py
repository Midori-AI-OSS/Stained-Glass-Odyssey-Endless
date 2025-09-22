"""Encrypted SQLCipher manager for the tracking database."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sys
from typing import Any, Final

if sys.platform == "win32":
    try:
        import pysqlcipher3.dbapi2 as sqlcipher3  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - limited Windows wheels fallback
        import sqlite3 as sqlcipher3  # type: ignore[assignment]

        def _noop_set_key(conn: Any, key: str) -> None:
            return None

        sqlcipher3.set_key = _noop_set_key  # type: ignore[attr-defined]
else:
    import sqlcipher3  # type: ignore[import-not-found]


SALT_FOR_KEY_DERIVATION: Final[bytes] = b"EndlessAutofighterTrackingSalt"


class TrackingDBManager:
    """Wrapper around SQLCipher connections for tracking telemetry."""

    def __init__(self, db_path: Path, key: str) -> None:
        self.db_path = Path(db_path)
        self.key = key

    @classmethod
    def from_env(cls) -> TrackingDBManager:
        base_path = Path(
            os.getenv("AF_TRACK_DB_PATH", Path(__file__).resolve().parent.parent / "track.db")
        )
        key = os.getenv("AF_DB_KEY")
        password = os.getenv("AF_DB_PASSWORD")
        if not key and password:
            key = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                SALT_FOR_KEY_DERIVATION,
                100_000,
                dklen=32,
            ).hex()
        return cls(base_path, key or "")

    @contextmanager
    def connection(self) -> Iterator[sqlcipher3.Connection]:  # type: ignore[name-defined]
        conn = sqlcipher3.connect(self.db_path)  # type: ignore[name-defined]
        try:
            if self.key:
                if hasattr(conn, "set_key"):
                    conn.set_key(self.key)
                else:
                    conn.execute("PRAGMA key = ?", (self.key,))
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def migrate(self, migrations_dir: Path) -> None:
        migrations = sorted(migrations_dir.glob("*.sql"))
        with self.connection() as conn:
            current = conn.execute("PRAGMA user_version").fetchone()[0]
            for path in migrations:
                prefix = path.stem.split("_")[0]
                if not prefix.isdigit():
                    continue
                version = int(prefix)
                if version <= current:
                    continue
                conn.executescript(path.read_text())
                conn.execute(f"PRAGMA user_version = {version}")


__all__ = ["TrackingDBManager", "sqlcipher3"]
