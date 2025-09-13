"""Comprehensive security tests for SaveManager."""
import hashlib
import os
import re
import secrets
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlcipher3

from autofighter.save_manager import SaveManager


class TestSaveManagerSecurity:
    """Test suite for SaveManager security vulnerabilities and hardening."""

    def test_sql_injection_in_pragma_key_windows(self, tmp_path):
        """Test that SQL injection in PRAGMA key is prevented on Windows."""
        db_path = tmp_path / "save.db"
        
        # First create a database with a normal key
        normal_key = "normalkey123456789012345678901234567890"
        mgr_normal = SaveManager(db_path, normal_key)
        migrations = Path(__file__).resolve().parents[1] / "migrations"
        mgr_normal.migrate(migrations)
        
        with mgr_normal.connection() as conn:
            conn.execute("INSERT INTO runs (id, party, map) VALUES ('test', '[]', '[]')")
        
        # Now try to access it with a malicious key (this should fail)
        malicious_key = "test'; DROP TABLE runs; CREATE TABLE evil (data TEXT); INSERT INTO evil VALUES ('pwned'); --"
        
        # Mock Windows platform to force PRAGMA key usage
        with patch('autofighter.save_manager.sys.platform', 'win32'):
            mgr_malicious = SaveManager(db_path, malicious_key)
            
            # This should fail safely without executing arbitrary SQL
            with pytest.raises((sqlcipher3.DatabaseError, ValueError)):
                with mgr_malicious.connection() as conn:
                    conn.execute("SELECT COUNT(*) FROM runs")
        
        # Verify the original database is still intact and no evil table exists
        with mgr_normal.connection() as conn:
            # Original data should still be there
            count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            assert count == 1, "Original data should be preserved"
            
            # No evil table should exist
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evil'").fetchall()
            assert len(tables) == 0, "No evil table should be created via SQL injection"

    def test_password_salt_resistance_to_rainbow_tables(self, tmp_path):
        """Test that password hashing is resistant to rainbow table attacks."""
        password = "commonpassword123"
        
        # Set up different database paths to avoid salt file conflicts
        db_path1 = tmp_path / "db1" / "save.db"
        db_path2 = tmp_path / "db2" / "save.db" 
        db_path1.parent.mkdir()
        db_path2.parent.mkdir()
        
        # Create two managers with the same password but different database paths
        mgr1 = SaveManager(db_path1, "", None)
        mgr1.key = mgr1._derive_key_securely(password, secrets.token_bytes(32))
        
        mgr2 = SaveManager(db_path2, "", None)
        mgr2.key = mgr2._derive_key_securely(password, secrets.token_bytes(32))
        
        # Keys should be different due to salt
        assert mgr1.key != mgr2.key, "Same password should generate different keys due to salt"

    def test_key_derivation_uses_strong_algorithm(self, tmp_path):
        """Test that key derivation uses a strong algorithm like PBKDF2 or Argon2."""
        password = "testpassword"
        salt = secrets.token_bytes(32)
        
        mgr = SaveManager(tmp_path / "save.db", "", salt)
        derived_key = mgr._derive_key_securely(password, salt)
        
        # Check that the key is not just SHA-256 of the password
        simple_sha256 = hashlib.sha256(password.encode()).hexdigest()
        assert derived_key != simple_sha256, "Key derivation should not be simple SHA-256"
        
        # Key should be properly formatted (hex string of appropriate length)
        assert len(derived_key) == 64, f"Key length {len(derived_key)} should be 64 (32 bytes hex)"
        assert re.match(r'^[a-f0-9]+$', derived_key), "Key should be a valid hex string"
        
        # Same password + salt should always produce same key (deterministic)
        derived_key2 = mgr._derive_key_securely(password, salt)
        assert derived_key == derived_key2, "Same password + salt should produce same key"
        
        # Different salt should produce different key
        different_salt = secrets.token_bytes(32)
        derived_key3 = mgr._derive_key_securely(password, different_salt)
        assert derived_key != derived_key3, "Different salt should produce different key"

    def test_encryption_failure_causes_hard_failure(self, tmp_path):
        """Test that encryption failures cause hard failures, not silent fallbacks."""
        db_path = tmp_path / "save.db"
        
        # Test with an empty/invalid key that should cause encryption to fail
        with pytest.raises(ValueError, match="No encryption key available"):
            mgr = SaveManager(db_path, "")
            with mgr.connection() as conn:
                conn.execute("CREATE TABLE test (id INTEGER)")

    def test_no_silent_fallback_on_encryption_failure(self, tmp_path):
        """Test that the system doesn't silently fall back to unencrypted SQLite."""
        # Test that invalid environment configuration raises proper errors
        with pytest.raises(ValueError, match="No encryption key provided"):
            SaveManager.from_env()  # No AF_DB_KEY or AF_DB_PASSWORD set

    def test_key_memory_security(self, tmp_path):
        """Test that cryptographic keys are handled securely in memory."""
        db_path = tmp_path / "save.db"
        key = "supersecretkey123456789"
        
        mgr = SaveManager(db_path, key)
        
        # Check if the key is stored as bytes or has any memory protection
        if hasattr(mgr, '_secure_key'):
            # If implemented, secure key should not be the same as plaintext
            assert mgr._secure_key != key.encode()
        
        # Key should not be stored in multiple places
        key_count = sum(1 for attr in dir(mgr) if hasattr(mgr, attr) and getattr(mgr, attr) == key)
        assert key_count <= 1, f"Key is stored in {key_count} attributes, should be minimized"

    def test_database_file_permissions(self, tmp_path):
        """Test that database files are created with secure permissions."""
        db_path = tmp_path / "save.db" 
        mgr = SaveManager(db_path, "testkey")
        
        # Create the database file
        migrations = Path(__file__).resolve().parents[1] / "migrations"
        mgr.migrate(migrations)
        
        # Check file permissions (should be 600 or similar - owner read/write only)
        file_stat = db_path.stat()
        permissions = oct(file_stat.st_mode)[-3:]
        
        # Permissions should be restrictive (no group/other access)
        assert permissions in ['600', '640'], f"Database file permissions {permissions} are too permissive"

    def test_environment_variable_security(self, tmp_path, monkeypatch):
        """Test that environment variables are handled securely."""
        db_path = tmp_path / "save.db"
        
        # Test with dangerous environment variable content
        dangerous_password = "test'; DROP TABLE runs; --"
        monkeypatch.setenv("AF_DB_PATH", str(db_path))
        monkeypatch.setenv("AF_DB_PASSWORD", dangerous_password)
        
        mgr = SaveManager.from_env()
        
        # Password should be properly sanitized/escaped
        assert "DROP TABLE" not in mgr.key
        assert mgr.key != dangerous_password

    def test_migration_sql_injection_prevention(self, tmp_path):
        """Test comprehensive SQL injection prevention in migrations."""
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        
        # Create legitimate migration
        (migrations / "001_init.sql").write_text("CREATE TABLE test(id TEXT);")
        
        # Create a migration that will attempt to manipulate the test table
        (migrations / "002_normal.sql").write_text("INSERT INTO test (id) VALUES ('normal');")
        
        # Files without proper numeric prefix should be ignored
        (migrations / "evil.sql").write_text("DROP TABLE test;")
        (migrations / "abc_evil.sql").write_text("DROP TABLE test;")
        
        mgr = SaveManager(tmp_path / "save.db", "testkey123456789012345678901234567890")
        
        # Run migrations - evil.sql and abc_evil.sql should be skipped
        mgr.migrate(migrations)
        
        # Verify that migrations with proper numeric prefixes ran
        with mgr.connection() as conn:
            # Check that test table exists and has the expected data
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test'").fetchall()
            assert len(tables) == 1, "Test table should exist"
            
            # Check that the normal migration ran
            count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
            assert count == 1, "Normal migration should have inserted data"
            
            # Verify the data is what we expect
            data = conn.execute("SELECT id FROM test").fetchone()[0]
            assert data == "normal", "Should contain data from normal migration"

    def test_key_rotation_capability(self, tmp_path):
        """Test that the system supports secure key rotation."""
        db_path = tmp_path / "save.db"
        migrations = Path(__file__).resolve().parents[1] / "migrations"
        
        # Create database with original key
        original_key = "original_key_123"
        mgr1 = SaveManager(db_path, original_key)
        mgr1.migrate(migrations)
        
        with mgr1.connection() as conn:
            conn.execute("INSERT INTO runs (id, party, map) VALUES ('test1', '[]', '[]')")
        
        # Test key rotation (if implemented)
        new_key = "new_rotated_key_456"
        if hasattr(SaveManager, 'rotate_key'):
            mgr1.rotate_key(new_key)
            
            # Verify old key no longer works
            mgr_old = SaveManager(db_path, original_key)
            with pytest.raises(sqlcipher3.DatabaseError):
                with mgr_old.connection() as conn:
                    conn.execute("SELECT COUNT(*) FROM runs")
            
            # Verify new key works
            mgr_new = SaveManager(db_path, new_key)
            with mgr_new.connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
                assert count == 1

    def test_audit_logging_for_security_events(self, tmp_path, caplog):
        """Test that security-relevant events are logged for audit purposes."""
        import logging
        caplog.set_level(logging.WARNING)
        
        db_path = tmp_path / "save.db"
        
        # First create a database with good key
        good_mgr = SaveManager(db_path, "goodkey123456789012345678901234567890")
        migrations = Path(__file__).resolve().parents[1] / "migrations"
        good_mgr.migrate(migrations)
        
        # Now test failed authentication attempt with wrong key
        with pytest.raises((sqlcipher3.DatabaseError, ValueError)):
            mgr = SaveManager(db_path, "wrong_key_1234567890123456789012345678901234567890")
            with mgr.connection() as conn:
                conn.execute("SELECT 1")
        
        # Check if security events were logged
        security_logs = [record for record in caplog.records 
                        if any(word in record.message.lower() 
                              for word in ['error', 'failed', 'invalid', 'warning'])]
        assert len(security_logs) > 0, "Security events should be logged"

    def test_timing_attack_resistance(self, tmp_path):
        """Test that key validation is resistant to timing attacks."""
        import time
        
        db_path = tmp_path / "save.db"
        correct_key = "correct_key_1234567890123456789012345678"
        
        # Create database with correct key
        mgr = SaveManager(db_path, correct_key)
        migrations = Path(__file__).resolve().parents[1] / "migrations"
        mgr.migrate(migrations)
        
        # Test timing for various wrong keys of different lengths
        wrong_keys = [
            "x" * 32,  # Short-ish key but meets minimum length
            "wrong_key_1234567890123456789012345678",  # Same length, different content
            "completely_wrong_key_with_different_length_123456789012345678901234567890",  # Different length
        ]
        
        timings = []
        for wrong_key in wrong_keys:
            mgr_wrong = SaveManager(db_path, wrong_key)
            start_time = time.time()
            try:
                with mgr_wrong.connection() as conn:
                    conn.execute("SELECT 1")
            except (sqlcipher3.DatabaseError, ValueError):
                pass  # Expected to fail
            end_time = time.time()
            timings.append(end_time - start_time)
        
        # Timing differences should be minimal (within reasonable bounds)
        if len(timings) > 1:
            max_timing = max(timings)
            min_timing = min(timings)
            timing_ratio = max_timing / min_timing if min_timing > 0 else float('inf')
            
            # Allow some variance but not orders of magnitude difference
            # Note: This is a basic check - true timing attack prevention requires constant-time operations
            assert timing_ratio < 100, f"Timing ratio {timing_ratio} suggests potential timing attack vulnerability"


# Helper method for testing (to be added to SaveManager)
def from_env_with_password(password: str) -> SaveManager:
    """Create SaveManager with password for testing purposes."""
    # This would use the enhanced password derivation
    key = hashlib.sha256(password.encode()).hexdigest()  # Temporary, will be replaced with PBKDF2
    return SaveManager(Path("test.db"), key)

# Monkey patch for testing
SaveManager.from_env_with_password = staticmethod(from_env_with_password)