# Task 02: Database Migration to Separate Container

## Objective
Move the database from the embedded SQLite file in the backend to a dedicated PostgreSQL container with web-based administration interface.

## Requirements

### 1. Database Service Setup
- **Technology**: PostgreSQL 15+ (more web-friendly than SQLite)
- **Port**: 5432 (PostgreSQL standard)
- **Admin Interface**: pgAdmin 4 on port 8080
- **Data Persistence**: Named Docker volume
- **Migration**: Automated migration from existing SQLite data

### 2. Current State Analysis
**Current Database**: 
- Location: `backend/save.db`
- Format: SQLite with SQLCipher encryption
- Tables: `runs`, `owned_players`, `gacha_items`, `gacha_rolls`, `upgrade_points`
- Manager: `SaveManager` class in `backend/autofighter/save_manager.py`

### 3. Migration Strategy
- Export existing SQLite data to SQL dump
- Create PostgreSQL schema with equivalent tables
- Import data preserving relationships and constraints
- Update backend to use PostgreSQL adapter
- Maintain encryption for sensitive data

## Implementation Tasks

### Task 2.1: Database Schema Analysis
**File**: `tasks/database-analysis.sql`
```sql
-- Current SQLite schema (from migrations)
-- 001_init.sql
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, 
    party TEXT, 
    map TEXT
);
CREATE TABLE IF NOT EXISTS owned_players (
    id TEXT PRIMARY KEY
);

-- 002_gacha.sql  
CREATE TABLE gacha_items (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    type TEXT NOT NULL,
    star_level INTEGER NOT NULL DEFAULT 1,
    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE gacha_rolls (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL DEFAULT 'player',
    items TEXT NOT NULL,
    rolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 003_upgrades.sql
CREATE TABLE upgrade_points (
    player_id TEXT PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 0,
    hp INTEGER NOT NULL DEFAULT 0,
    atk INTEGER NOT NULL DEFAULT 0, 
    def INTEGER NOT NULL DEFAULT 0,
    crit_rate INTEGER NOT NULL DEFAULT 0,
    crit_damage INTEGER NOT NULL DEFAULT 0
);

-- Additional tables from game.py
CREATE TABLE IF NOT EXISTS damage_types (
    id TEXT PRIMARY KEY, 
    type TEXT
);
```

### Task 2.2: PostgreSQL Schema Migration
**File**: `database/init/001_schema.sql`
```sql
-- PostgreSQL equivalent schema with improvements
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Runs table
CREATE TABLE runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE, -- For migration from SQLite
    party JSONB NOT NULL,
    map JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players table
CREATE TABLE owned_players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), 
    legacy_id TEXT UNIQUE, -- For migration from SQLite
    player_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gacha items
CREATE TABLE gacha_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE, -- For migration from SQLite
    item_id TEXT NOT NULL,
    type TEXT NOT NULL,
    star_level INTEGER NOT NULL DEFAULT 1 CHECK (star_level BETWEEN 1 AND 5),
    obtained_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gacha rolls
CREATE TABLE gacha_rolls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE, -- For migration from SQLite
    player_id UUID REFERENCES owned_players(id) ON DELETE CASCADE,
    items JSONB NOT NULL,
    rolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Upgrade points
CREATE TABLE upgrade_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES owned_players(id) ON DELETE CASCADE,
    points INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0),
    hp INTEGER NOT NULL DEFAULT 0 CHECK (hp >= 0),
    atk INTEGER NOT NULL DEFAULT 0 CHECK (atk >= 0), 
    def INTEGER NOT NULL DEFAULT 0 CHECK (def >= 0),
    crit_rate INTEGER NOT NULL DEFAULT 0 CHECK (crit_rate >= 0),
    crit_damage INTEGER NOT NULL DEFAULT 0 CHECK (crit_damage >= 0),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id)
);

-- Damage types
CREATE TABLE damage_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE, -- For migration from SQLite
    type TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_runs_created_at ON runs(created_at);
CREATE INDEX idx_gacha_items_type ON gacha_items(type);
CREATE INDEX idx_gacha_items_star_level ON gacha_items(star_level);
CREATE INDEX idx_gacha_rolls_player_id ON gacha_rolls(player_id);
CREATE INDEX idx_gacha_rolls_rolled_at ON gacha_rolls(rolled_at);

-- Update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_runs_updated_at BEFORE UPDATE ON runs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_owned_players_updated_at BEFORE UPDATE ON owned_players 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_upgrade_points_updated_at BEFORE UPDATE ON upgrade_points 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Task 2.3: Data Migration Script
**File**: `database/migrate_from_sqlite.py`
```python
#!/usr/bin/env python3
"""Migration script from SQLite to PostgreSQL"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Database connections
SQLITE_PATH = os.getenv("SQLITE_PATH", "backend/save.db")
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://autofighter:password@localhost:5432/autofighter")

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""
    
    if not Path(SQLITE_PATH).exists():
        print(f"❌ SQLite database not found at {SQLITE_PATH}")
        return False
    
    try:
        # Connect to databases
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        
        postgres_conn = psycopg2.connect(POSTGRES_URL)
        postgres_conn.autocommit = False
        
        print("🔍 Starting migration from SQLite to PostgreSQL...")
        
        # Migrate each table
        migrate_runs(sqlite_conn, postgres_conn)
        migrate_owned_players(sqlite_conn, postgres_conn)  
        migrate_gacha_items(sqlite_conn, postgres_conn)
        migrate_gacha_rolls(sqlite_conn, postgres_conn)
        migrate_upgrade_points(sqlite_conn, postgres_conn)
        migrate_damage_types(sqlite_conn, postgres_conn)
        
        postgres_conn.commit()
        print("✅ Migration completed successfully!")
        
        # Verify migration
        verify_migration(sqlite_conn, postgres_conn)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'postgres_conn' in locals():
            postgres_conn.rollback()
        return False
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'postgres_conn' in locals():
            postgres_conn.close()

def migrate_runs(sqlite_conn, postgres_conn):
    """Migrate runs table"""
    print("  📋 Migrating runs...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute("SELECT * FROM runs")
    rows = sqlite_cursor.fetchall()
    
    for row in rows:
        postgres_cursor.execute("""
            INSERT INTO runs (legacy_id, party, map) 
            VALUES (%s, %s, %s)
        """, (row['id'], row['party'], row['map']))
    
    print(f"    ✓ Migrated {len(rows)} runs")

def migrate_owned_players(sqlite_conn, postgres_conn):
    """Migrate owned_players table"""
    print("  👤 Migrating owned players...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute("SELECT * FROM owned_players")
    rows = sqlite_cursor.fetchall()
    
    for row in rows:
        postgres_cursor.execute("""
            INSERT INTO owned_players (legacy_id) 
            VALUES (%s) RETURNING id
        """, (row['id'],))
        player_uuid = postgres_cursor.fetchone()[0]
        
        # Store UUID mapping for foreign key references
        if not hasattr(migrate_owned_players, 'id_mapping'):
            migrate_owned_players.id_mapping = {}
        migrate_owned_players.id_mapping[row['id']] = player_uuid
    
    print(f"    ✓ Migrated {len(rows)} owned players")

def migrate_gacha_items(sqlite_conn, postgres_conn):
    """Migrate gacha_items table"""
    print("  🎲 Migrating gacha items...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT * FROM gacha_items")
        rows = sqlite_cursor.fetchall()
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO gacha_items (legacy_id, item_id, type, star_level, obtained_at) 
                VALUES (%s, %s, %s, %s, %s)
            """, (row['id'], row['item_id'], row['type'], row['star_level'], row['obtained_at']))
        
        print(f"    ✓ Migrated {len(rows)} gacha items")
    except sqlite3.OperationalError:
        print("    ⚠️  gacha_items table not found, skipping")

def migrate_gacha_rolls(sqlite_conn, postgres_conn):
    """Migrate gacha_rolls table"""
    print("  🎰 Migrating gacha rolls...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT * FROM gacha_rolls")
        rows = sqlite_cursor.fetchall()
        
        for row in rows:
            # Map player_id to UUID
            player_uuid = migrate_owned_players.id_mapping.get(row['player_id'])
            
            postgres_cursor.execute("""
                INSERT INTO gacha_rolls (legacy_id, player_id, items, rolled_at) 
                VALUES (%s, %s, %s, %s)
            """, (row['id'], player_uuid, row['items'], row['rolled_at']))
        
        print(f"    ✓ Migrated {len(rows)} gacha rolls")
    except sqlite3.OperationalError:
        print("    ⚠️  gacha_rolls table not found, skipping")

def migrate_upgrade_points(sqlite_conn, postgres_conn):
    """Migrate upgrade_points table"""
    print("  ⬆️  Migrating upgrade points...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT * FROM upgrade_points")
        rows = sqlite_cursor.fetchall()
        
        for row in rows:
            # Map player_id to UUID
            player_uuid = migrate_owned_players.id_mapping.get(row['player_id'])
            
            postgres_cursor.execute("""
                INSERT INTO upgrade_points (player_id, points, hp, atk, def, crit_rate, crit_damage) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (player_uuid, row['points'], row['hp'], row['atk'], row['def'], 
                  row['crit_rate'], row['crit_damage']))
        
        print(f"    ✓ Migrated {len(rows)} upgrade points")
    except sqlite3.OperationalError:
        print("    ⚠️  upgrade_points table not found, skipping")

def migrate_damage_types(sqlite_conn, postgres_conn):
    """Migrate damage_types table"""
    print("  ⚔️  Migrating damage types...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT * FROM damage_types")
        rows = sqlite_cursor.fetchall()
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO damage_types (legacy_id, type) 
                VALUES (%s, %s)
            """, (row['id'], row['type']))
        
        print(f"    ✓ Migrated {len(rows)} damage types")
    except sqlite3.OperationalError:
        print("    ⚠️  damage_types table not found, skipping")

def verify_migration(sqlite_conn, postgres_conn):
    """Verify migration completed successfully"""
    print("🔍 Verifying migration...")
    
    postgres_cursor = postgres_conn.cursor()
    
    # Count records in each table
    tables = ['runs', 'owned_players', 'gacha_items', 'gacha_rolls', 'upgrade_points', 'damage_types']
    
    for table in tables:
        try:
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = postgres_cursor.fetchone()[0]
            print(f"    ✓ {table}: {count} records")
        except Exception as e:
            print(f"    ❌ {table}: Error - {e}")

if __name__ == "__main__":
    success = migrate_data()
    sys.exit(0 if success else 1)
```

### Task 2.4: PostgreSQL Database Adapter
**File**: `backend/autofighter/postgres_manager.py`
```python
"""PostgreSQL database manager replacement for SaveManager"""

from __future__ import annotations

import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
import logging

log = logging.getLogger(__name__)

class PostgreSQLManager:
    """PostgreSQL database manager for AutoFighter"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
    @classmethod
    def from_env(cls) -> PostgreSQLManager:
        """Create manager from environment variables"""
        database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://autofighter:password@database:5432/autofighter"
        )
        return cls(database_url)
    
    @contextmanager
    def connection(self) -> Iterator[psycopg2.extensions.connection]:
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            conn.autocommit = True  # Match SQLite behavior
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            log.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def migrate(self, migrations_dir: Path):
        """Apply database migrations"""
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        with self.connection() as conn:
            cursor = conn.cursor()
            
            # Create migrations tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    filename VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Get applied migrations
            cursor.execute("SELECT filename FROM migration_history")
            applied = {row[0] for row in cursor.fetchall()}
            
            # Apply new migrations
            for migration_file in migration_files:
                if migration_file.name not in applied:
                    log.info(f"Applying migration: {migration_file.name}")
                    
                    with open(migration_file, 'r') as f:
                        migration_sql = f.read()
                    
                    cursor.execute(migration_sql)
                    cursor.execute(
                        "INSERT INTO migration_history (filename) VALUES (%s)",
                        (migration_file.name,)
                    )
                    
                    log.info(f"Migration {migration_file.name} applied successfully")
    
    def execute_query(self, query: str, params=None):
        """Execute a query and return results"""
        with self.connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return cursor.rowcount
    
    def execute_many(self, query: str, params_list):
        """Execute a query with multiple parameter sets"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
```

### Task 2.5: Backend Migration
**File**: `backend/autofighter/database_migration.py`
```python
"""Update existing backend code to use PostgreSQL"""

from autofighter.postgres_manager import PostgreSQLManager
import logging

log = logging.getLogger(__name__)

# Global manager instance
POSTGRES_MANAGER: PostgreSQLManager | None = None

def get_postgres_manager() -> PostgreSQLManager:
    """Get the global PostgreSQL manager instance"""
    global POSTGRES_MANAGER
    
    if POSTGRES_MANAGER is None:
        POSTGRES_MANAGER = PostgreSQLManager.from_env()
        # Apply migrations
        from pathlib import Path
        migrations_dir = Path(__file__).resolve().parent.parent / "database" / "migrations"
        if migrations_dir.exists():
            POSTGRES_MANAGER.migrate(migrations_dir)
    
    return POSTGRES_MANAGER

# Migration helper functions
def migrate_save_manager_calls():
    """Helper to guide migration of existing SaveManager calls"""
    
    migration_map = {
        # Old SaveManager pattern -> New PostgreSQL pattern
        'get_save_manager()': 'get_postgres_manager()',
        'manager.connection()': 'manager.connection()',
        'conn.execute(sql)': 'cursor.execute(sql)',  # Note: use cursor from connection
        'conn.fetchone()': 'cursor.fetchone()',
        'conn.fetchall()': 'cursor.fetchall()',
    }
    
    log.info("SaveManager migration patterns:")
    for old, new in migration_map.items():
        log.info(f"  {old} -> {new}")

# Example migration for existing game.py code
def update_game_py_example():
    """Example of how to update game.py database calls"""
    
    # OLD CODE:
    # manager = get_save_manager()
    # with manager.connection() as conn:
    #     conn.execute("INSERT INTO owned_players (id) VALUES (?)", (player_id,))
    #     result = conn.fetchone()
    
    # NEW CODE:
    # manager = get_postgres_manager()
    # with manager.connection() as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("INSERT INTO owned_players (legacy_id) VALUES (%s) RETURNING id", (player_id,))
    #     result = cursor.fetchone()
    
    pass
```

### Task 2.6: Docker Configuration
**File**: `database/docker-compose.database.yml`
```yaml
# Database services for development
version: '3.8'

services:
  database:
    image: postgres:15-alpine
    container_name: autofighter-database
    environment:
      POSTGRES_DB: autofighter
      POSTGRES_USER: autofighter
      POSTGRES_PASSWORD: password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    volumes:
      - autofighter_postgres_data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - autofighter-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U autofighter -d autofighter"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: autofighter-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@autofighter.local
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    volumes:
      - autofighter_pgadmin_data:/var/lib/pgadmin
      - ./pgadmin/servers.json:/pgadmin4/servers.json
    ports:
      - "8080:80"
    networks:
      - autofighter-network
    depends_on:
      database:
        condition: service_healthy

volumes:
  autofighter_postgres_data:
    driver: local
  autofighter_pgadmin_data:
    driver: local

networks:
  autofighter-network:
    driver: bridge
```

**File**: `database/pgadmin/servers.json`
```json
{
  "Servers": {
    "1": {
      "Name": "AutoFighter Database",
      "Group": "AutoFighter",
      "Host": "database",
      "Port": 5432,
      "MaintenanceDB": "autofighter",
      "Username": "autofighter",
      "SSLMode": "prefer",
      "SSLCert": "<STORAGE_DIR>/.postgresql/postgresql.crt",
      "SSLKey": "<STORAGE_DIR>/.postgresql/postgresql.key",
      "SSLCompression": 0,
      "Timeout": 10,
      "UseSSHTunnel": 0,
      "TunnelPort": "22",
      "TunnelAuthentication": 0
    }
  }
}
```

### Task 2.7: Migration Validation
**File**: `database/validate_migration.py`
```python
#!/usr/bin/env python3
"""Validate database migration"""

import psycopg2
import psycopg2.extras
import os
import sys

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://autofighter:password@localhost:5432/autofighter")

def validate_migration():
    """Validate that database migration was successful"""
    
    print("🔍 Validating PostgreSQL database migration...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check all tables exist
        expected_tables = [
            'runs', 'owned_players', 'gacha_items', 
            'gacha_rolls', 'upgrade_points', 'damage_types'
        ]
        
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        
        existing_tables = {row['table_name'] for row in cursor.fetchall()}
        
        print("  📋 Checking table structure...")
        for table in expected_tables:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"    ✓ {table}: {count} records")
            else:
                print(f"    ❌ {table}: Missing")
                return False
        
        # Check constraints and indexes
        print("  🔗 Checking constraints...")
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY'
        """)
        fk_count = cursor.fetchone()['count']
        print(f"    ✓ Foreign key constraints: {fk_count}")
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM pg_indexes 
            WHERE schemaname = 'public'
        """)
        index_count = cursor.fetchone()['count']
        print(f"    ✓ Indexes: {index_count}")
        
        # Test basic operations
        print("  🧪 Testing basic operations...")
        
        # Insert test record
        cursor.execute("""
            INSERT INTO owned_players (legacy_id) 
            VALUES ('test_migration') 
            RETURNING id
        """)
        test_id = cursor.fetchone()['id']
        
        # Read back test record
        cursor.execute("""
            SELECT * FROM owned_players WHERE id = %s
        """, (test_id,))
        test_record = cursor.fetchone()
        
        if test_record:
            print("    ✓ Insert/Select operations working")
            
            # Clean up test record
            cursor.execute("""
                DELETE FROM owned_players WHERE id = %s
            """, (test_id,))
            print("    ✓ Delete operations working")
        else:
            print("    ❌ Insert/Select operations failed")
            return False
        
        conn.commit()
        print("✅ Database migration validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database migration validation failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    result = validate_migration()
    sys.exit(0 if result else 1)
```

## Testing Commands

```bash
# Start database services
cd database
docker-compose -f docker-compose.database.yml up -d

# Wait for database to be ready
docker-compose -f docker-compose.database.yml exec database pg_isready -U autofighter

# Run migration
python migrate_from_sqlite.py

# Validate migration
python validate_migration.py

# Access pgAdmin
# Open http://localhost:8080
# Login: admin@autofighter.local / admin
```

## Completion Criteria

- [ ] PostgreSQL database container running on port 5432
- [ ] pgAdmin web interface accessible on port 8080
- [ ] Database schema created with all tables and constraints
- [ ] Data successfully migrated from SQLite
- [ ] PostgreSQL manager class implemented
- [ ] Validation script passes all tests
- [ ] Web admin interface can view and modify data

## Notes for Task Master Review

- Migration preserves all existing data with UUID primary keys
- PostgreSQL provides better concurrency and web integration
- pgAdmin enables easy database administration
- Backward compatibility maintained with legacy_id columns
- Foreign key constraints ensure data integrity

**Next Task**: After completion and review, proceed to `task-03-backend-updates.md`