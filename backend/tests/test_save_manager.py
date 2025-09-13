import hashlib
from pathlib import Path

import pytest
import sqlcipher3

from autofighter.save_manager import SaveManager


def test_password_derives_key(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    migrations = Path(__file__).resolve().parents[1] / "migrations"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_PASSWORD", "secret")
    mgr = SaveManager.from_env()
    
    # With the new security improvements, keys are derived with PBKDF2 + salt
    # so they won't match the simple SHA-256
    assert mgr.key != hashlib.sha256(b"secret").hexdigest(), "Should use secure key derivation, not plain SHA-256"
    assert len(mgr.key) == 64, "Key should be 32 bytes (64 hex chars)"
    
    mgr.migrate(migrations)
    with mgr.connection() as conn:
        conn.execute(
            "INSERT INTO runs (id, party, map) VALUES ('1', '[]', '[]')"
        )
        version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == 3
    
    # Test that the same password can recreate the manager and access data
    mgr2 = SaveManager.from_env()
    with mgr2.connection() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM runs")
        assert cur.fetchone()[0] == 1
    
    # Test that wrong key fails properly
    bad_mgr = SaveManager(db_path, "badkey")
    with pytest.raises((sqlcipher3.DatabaseError, ValueError)):
        with bad_mgr.connection() as conn:
            conn.execute("SELECT COUNT(*) FROM runs")


def test_malformed_key_does_not_execute_sql(tmp_path):
    db_path = tmp_path / "save.db"
    migrations = Path(__file__).resolve().parents[1] / "migrations"
    mgr = SaveManager(db_path, "goodkey")
    mgr.migrate(migrations)
    with mgr.connection() as conn:
        conn.execute(
            "INSERT INTO runs (id, party, map) VALUES ('1', '[]', '[]')"
        )

    malicious_key = "x'; DROP TABLE runs;--"
    bad_mgr = SaveManager(db_path, malicious_key)
    # With the new security improvements, malicious keys are escaped and 
    # will result in invalid encryption key errors instead of SQL injection
    with pytest.raises((sqlcipher3.DatabaseError, ValueError)):
        with bad_mgr.connection() as conn:
            conn.execute("SELECT COUNT(*) FROM runs")

    # Verify original data is still intact with correct key
    with mgr.connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert count == 1


def test_migration_filename_injection_ignored(tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_init.sql").write_text(
        "CREATE TABLE runs(id TEXT);"
    )
    # Attempt to inject SQL via the migration filename. Because the prefix isn't
    # purely numeric, the migration should be skipped.
    (migrations / "1; DROP TABLE runs;--_evil.sql").write_text(
        "DROP TABLE runs;"
    )
    mgr = SaveManager(tmp_path / "save.db", "goodkey")
    mgr.migrate(migrations)
    with mgr.connection() as conn:
        conn.execute("INSERT INTO runs (id) VALUES ('1')")
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert count == 1
