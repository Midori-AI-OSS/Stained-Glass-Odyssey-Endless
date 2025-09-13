# SaveManager Security Features

## Overview
The SaveManager implements multiple layers of security to protect encrypted database files. The system is designed to be "incredibly difficult to hack" with defense-in-depth security measures.

## Security Features

### 1. Strong Cryptographic Key Derivation
- **PBKDF2 with SHA-256**: Uses industry-standard PBKDF2 algorithm instead of plain SHA-256
- **100,000 iterations**: Meets OWASP recommendations for password-based key derivation
- **256-bit salt**: Cryptographically secure random salt prevents rainbow table attacks
- **Unique keys**: Same password generates different keys across different databases

### 2. SQL Injection Prevention
- **Proper quote escaping**: PRAGMA key statements use SQL standard quote escaping (double quotes)
- **Input validation**: Database keys are validated for format and minimum length
- **Migration filename validation**: Only numeric prefixes allowed to prevent injection in version setting

### 3. No Silent Fallbacks
- **Hard encryption requirement**: System fails completely if SQLCipher is not available
- **Windows security**: Eliminated dangerous fallback to unencrypted SQLite on Windows
- **Error visibility**: All encryption failures are properly reported, not silently ignored

### 4. Secure File Handling
- **Restricted permissions**: Database files automatically set to 600 (owner read/write only)
- **Salt file protection**: Salt files protected with secure permissions
- **Automatic permission enforcement**: Permissions verified and set on every database access

### 5. Comprehensive Audit Logging
- **Security event logging**: Failed authentication attempts and encryption errors logged
- **Migration logging**: All migration operations logged with success/failure status
- **Error details**: Detailed error information for debugging while protecting sensitive data

### 6. Defense in Depth
- **Multiple validation layers**: Key validation, encryption verification, and access controls
- **Fail-safe defaults**: System fails securely rather than operating in degraded mode
- **Backward compatibility**: Existing databases continue to work while encouraging migration to new security

## Security Architecture

### Key Storage and Management
```
Password (user input)
    ↓
PBKDF2-SHA256 (100k iterations) + 256-bit salt
    ↓
32-byte derived key (stored as 64-char hex)
    ↓
SQLCipher encryption key
```

### File Structure
```
/path/to/save.db      # Encrypted database (permissions: 600)
/path/to/save.salt    # Salt file (permissions: 600)
```

### Authentication Flow
1. User provides password via AF_DB_PASSWORD environment variable
2. System loads or generates 256-bit cryptographic salt
3. PBKDF2 derives encryption key from password + salt
4. SQLCipher attempts to open database with derived key
5. System verifies encryption is working with test query
6. Connection established or hard failure with audit logging

## Threat Model

### Threats Mitigated
- **SQL Injection**: Proper escaping prevents malicious code execution
- **Rainbow Table Attacks**: Salt + PBKDF2 makes precomputed attacks infeasible
- **Dictionary Attacks**: 100,000 iterations significantly slow brute force attempts
- **File System Access**: Restricted permissions prevent unauthorized access
- **Silent Failures**: All security failures are detected and reported
- **Cryptographic Weaknesses**: Modern algorithms replace legacy approaches

### Remaining Considerations
- **Key Management**: Users responsible for secure password storage
- **Memory Security**: Keys exist in memory during operation (industry standard)
- **Side Channel Attacks**: Timing attack resistance is basic, not constant-time
- **Physical Access**: File encryption protects against disk access, not live memory

## Usage Examples

### Environment Setup
```bash
# Set database password (recommended)
export AF_DB_PASSWORD="your-secure-password"

# Or set pre-derived key (advanced)
export AF_DB_KEY="your-64-character-hex-key"

# Optional: Set custom database path
export AF_DB_PATH="/secure/path/to/database.db"
```

### Programmatic Usage
```python
from autofighter.save_manager import SaveManager

# Use environment variables (recommended)
mgr = SaveManager.from_env()

# Or specify key directly
mgr = SaveManager(Path("database.db"), "your-key")

# Migrate and use database
mgr.migrate(Path("migrations"))
with mgr.connection() as conn:
    conn.execute("INSERT INTO table VALUES (?)", ("data",))
```

## Security Validation

The system includes comprehensive security tests that validate:
- SQL injection prevention
- Strong key derivation
- Encryption failure handling
- File permission security
- Audit logging functionality
- Migration security
- Timing attack resistance

Run security tests with:
```bash
pytest tests/test_save_manager_security.py -v
```

## Compliance and Standards

The implementation follows security best practices:
- **OWASP**: Password storage guidelines (PBKDF2, iterations, salt)
- **NIST**: Cryptographic standards (approved algorithms)
- **SQL Standards**: Proper escaping techniques
- **UNIX Security**: Least-privilege file permissions
- **Defense in Depth**: Multiple independent security controls