from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import logging
import os
from pathlib import Path
import secrets
import stat
import sys

# Handle platform-specific SQLite encryption imports
if sys.platform == 'win32':
    try:
        import pysqlcipher3.dbapi2 as sqlcipher3
    except ImportError:
        # DO NOT FALLBACK TO UNENCRYPTED SQLITE - This is a security risk
        raise ImportError(
            "SQLCipher is required but not available. "
            "Install pysqlcipher3 for encrypted database support. "
            "Falling back to unencrypted SQLite is not permitted for security reasons."
        ) from None
else:
    import sqlcipher3

# For secure key derivation
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class SaveManager:
    """Wrapper around SQLCipher connections with enhanced security.

    Keys are read from ``AF_DB_KEY`` or derived from ``AF_DB_PASSWORD`` using PBKDF2.
    """

    def __init__(self, db_path: Path, key: str, salt: bytes | None = None) -> None:
        self.db_path = Path(db_path)
        self.key = key
        self.salt = salt
        self._log = logging.getLogger(__name__)
        
        # Set secure file permissions on database file if it exists
        self._ensure_secure_permissions()

    def _ensure_secure_permissions(self) -> None:
        """Ensure database file has secure permissions (owner read/write only)."""
        if self.db_path.exists():
            # Set permissions to 600 (owner read/write only)
            self.db_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def _derive_key_securely(self, password: str, salt: bytes) -> str:
        """Derive a cryptographic key from password using PBKDF2."""
        if not CRYPTO_AVAILABLE:
            self._log.warning(
                "Cryptography library not available. Falling back to SHA-256. "
                "Install 'cryptography' package for enhanced security."
            )
            # Include salt in SHA-256 as minimal improvement
            return hashlib.sha256(salt + password.encode()).hexdigest()
        
        # Use PBKDF2 with SHA-256, 100,000 iterations (OWASP recommended minimum)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits
            salt=salt,
            iterations=100000,
        )
        key_bytes = kdf.derive(password.encode())
        return key_bytes.hex()

    @classmethod
    def from_env(cls) -> SaveManager:
        db_path = Path(
            os.getenv("AF_DB_PATH", Path(__file__).resolve().parent.parent / "save.db")
        )
        key = os.getenv("AF_DB_KEY")
        password = os.getenv("AF_DB_PASSWORD")
        
        if not key and password:
            # For password-based encryption, we need to store/retrieve the salt
            # Store salt in a companion file with the database
            salt_path = db_path.with_suffix('.salt')
            
            if salt_path.exists():
                # Use existing salt
                salt = salt_path.read_bytes()
                instance = cls(db_path, "", salt)
                key = instance._derive_key_securely(password, salt)
            else:
                # Check if database exists with old key derivation
                old_key = hashlib.sha256(password.encode()).hexdigest()
                if db_path.exists():
                    # Try old key first for backward compatibility
                    try:
                        test_mgr = cls(db_path, old_key, None)
                        with test_mgr.connection() as conn:
                            conn.execute("SELECT 1").fetchone()
                        # Old key works, use it (but log a warning)
                        logging.getLogger(__name__).warning(
                            "Using legacy key derivation. Consider migrating to PBKDF2 for enhanced security."
                        )
                        return test_mgr
                    except sqlcipher3.DatabaseError:
                        pass  # Old key doesn't work, create new salt
                
                # Generate a new secure random salt for new databases
                salt = secrets.token_bytes(32)  # 256-bit salt
                # Store salt securely (only readable by owner)
                salt_path.write_bytes(salt)
                salt_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
                
                instance = cls(db_path, "", salt)
                key = instance._derive_key_securely(password, salt)
            
            instance.key = key
            return instance
        elif key:
            # Validate key format
            if not isinstance(key, str) or len(key) < 32:
                raise ValueError("Invalid key format. Key must be at least 32 characters.")
            return cls(db_path, key, None)
        else:
            raise ValueError(
                "No encryption key provided. Set AF_DB_KEY or AF_DB_PASSWORD environment variable."
            )

    @contextmanager
    def connection(self) -> Iterator[sqlcipher3.Connection]:
        if not self.key:
            raise ValueError("No encryption key available. Database cannot be opened without encryption.")
        
        conn = sqlcipher3.connect(self.db_path)
        try:
            # Set encryption key securely
            if hasattr(conn, 'set_key'):
                # Use the secure set_key method if available
                conn.set_key(self.key)
            else:
                # For Windows/pysqlcipher3, use PRAGMA with proper escaping
                # Escape single quotes by doubling them (SQL standard)
                escaped_key = self.key.replace("'", "''")
                conn.execute(f"PRAGMA key = '{escaped_key}'")
            
            # Test that encryption is working by attempting a simple operation
            try:
                conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
            except sqlcipher3.DatabaseError as e:
                self._log.error("Database encryption verification failed: %s", e)
                raise ValueError("Invalid encryption key or corrupted database") from e
            
            # Set secure SQLite pragmas
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            conn.execute("PRAGMA secure_delete = ON")  # Securely delete data
            
            yield conn
            conn.commit()
        except Exception as e:
            # Log security event
            self._log.warning("Database connection failed: %s", e)
            conn.rollback()
            raise
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
                    self._log.warning("Skipping migration file with invalid name: %s", path.name)
                    continue
                
                try:
                    version = int(version_part)
                except ValueError:
                    self._log.warning("Skipping migration file with invalid version: %s", path.name)
                    continue
                
                if version <= current:
                    continue
                
                self._log.info("Running migration %s (version %d)", path.name, version)
                
                try:
                    # Validate migration content before execution
                    migration_content = path.read_text()
                    if not migration_content.strip():
                        self._log.warning("Skipping empty migration: %s", path.name)
                        continue
                    
                    conn.executescript(migration_content)
                    # ``PRAGMA user_version`` doesn't support parameter substitution.
                    # ``version`` is sanitized above (must be integer), so this is safe.
                    conn.execute(f"PRAGMA user_version = {version}")
                    self._log.info("Successfully applied migration %s", path.name)
                    
                except Exception as e:
                    self._log.error("Migration %s failed: %s", path.name, e)
                    raise RuntimeError(f"Migration {path.name} failed: {e}") from e
