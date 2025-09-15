from __future__ import annotations


def get_option(key: str, default: str | None = None) -> str | None:
    # Import lazily to avoid circular import during module initialization
    from runs.encryption import get_save_manager
    with get_save_manager().connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)")
        cur = conn.execute("SELECT value FROM options WHERE key = ?", (key,))
        row = cur.fetchone()
    if row is None:
        return default
    return row[0]


def set_option(key: str, value: str) -> None:
    # Import lazily to avoid circular import during module initialization
    from runs.encryption import get_save_manager
    with get_save_manager().connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)", (key, value))
