# Encrypted Save System

1. Store run and player data in SQLite secured with SQLCipher.
2. Minimize I/O via batched writes and compact schemas; supply migration tooling for legacy saves.
3. Derive SQLCipher keys from a user-supplied salted password stored in encrypted config with optional cloud backup.
4. Consider alternative key sources (OS keyrings, env vars, hardware tokens) for advanced setups.
5. Code structure:
   - Wrap database access in a `SaveManager` module with context-managed sessions.
   - Provide schema migrations using simple versioned scripts to keep saves forward compatible.
