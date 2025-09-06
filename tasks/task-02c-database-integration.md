# Task 2C: Database Integration

## Overview

This task integrates the PostgreSQL database with the backend service, replacing the SQLite-based SaveManager with a PostgreSQL adapter while maintaining API compatibility.

## Goals

- Create PostgreSQL database adapter for backend
- Replace SaveManager with PostgreSQL implementation
- Maintain existing API contracts and functionality
- Add connection pooling and error handling
- Implement database health checks

## Prerequisites

- Task 2A (Database Setup) must be completed
- Task 2B (Database Migration) must be completed
- PostgreSQL container running with migrated data
- Backend service structure in place

## Implementation

### Step 1: PostgreSQL Adapter

**File**: `backend/autofighter/database/__init__.py`
```python
"""Database package for PostgreSQL integration."""

from .adapter import PostgreSQLAdapter
from .models import *

__all__ = ["PostgreSQLAdapter"]
```

**File**: `backend/autofighter/database/adapter.py`
```python
"""PostgreSQL database adapter for AutoFighter."""

import asyncio
import asyncpg
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager
import uuid

logger = logging.getLogger(__name__)

class PostgreSQLAdapter:
    """PostgreSQL database adapter with async support."""
    
    def __init__(self, connection_string: str, pool_size: int = 10):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=self.pool_size,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool initialized")
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                
                # Get pool status
                pool_status = {
                    "size": self.pool.get_size(),
                    "idle": self.pool.get_idle_size(),
                    "used": self.pool.get_size() - self.pool.get_idle_size()
                }
                
                return {
                    "healthy": True,
                    "pool": pool_status,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Runs table operations
    async def save_run(self, run_id: str, party: Dict[str, Any], map_data: Dict[str, Any]) -> str:
        """Save a game run."""
        async with self.get_connection() as conn:
            # Check if run exists (by legacy_id)
            existing = await conn.fetchrow(
                "SELECT id FROM runs WHERE legacy_id = $1",
                run_id
            )
            
            if existing:
                # Update existing run
                await conn.execute("""
                    UPDATE runs 
                    SET party = $1, map = $2, updated_at = $3
                    WHERE legacy_id = $4
                """, json.dumps(party), json.dumps(map_data), datetime.now(), run_id)
                return str(existing['id'])
            else:
                # Insert new run
                new_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO runs (id, legacy_id, party, map, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, new_id, run_id, json.dumps(party), json.dumps(map_data), datetime.now(), datetime.now())
                return new_id
    
    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a game run by ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM runs WHERE legacy_id = $1 OR id::text = $1",
                run_id
            )
            
            if row:
                return {
                    "id": row['legacy_id'] or str(row['id']),
                    "party": json.loads(row['party']) if row['party'] else {},
                    "map": json.loads(row['map']) if row['map'] else {},
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                }
            return None
    
    async def list_runs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List game runs."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM runs 
                ORDER BY updated_at DESC 
                LIMIT $1 OFFSET $2
            """, limit, offset)
            
            return [
                {
                    "id": row['legacy_id'] or str(row['id']),
                    "party": json.loads(row['party']) if row['party'] else {},
                    "map": json.loads(row['map']) if row['map'] else {},
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                }
                for row in rows
            ]
    
    # Owned players operations
    async def save_owned_player(self, player_id: str, player_data: Dict[str, Any] = None) -> str:
        """Save an owned player."""
        async with self.get_connection() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM owned_players WHERE legacy_id = $1",
                player_id
            )
            
            if existing:
                if player_data:
                    await conn.execute("""
                        UPDATE owned_players 
                        SET player_data = $1
                        WHERE legacy_id = $2
                    """, json.dumps(player_data), player_id)
                return str(existing['id'])
            else:
                new_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO owned_players (id, legacy_id, player_data, created_at)
                    VALUES ($1, $2, $3, $4)
                """, new_id, player_id, json.dumps(player_data or {}), datetime.now())
                return new_id
    
    async def get_owned_players(self) -> List[str]:
        """Get list of owned player IDs."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("SELECT legacy_id FROM owned_players")
            return [row['legacy_id'] for row in rows if row['legacy_id']]
    
    async def has_owned_player(self, player_id: str) -> bool:
        """Check if player is owned."""
        async with self.get_connection() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM owned_players WHERE legacy_id = $1",
                player_id
            )
            return result > 0
    
    # Gacha operations
    async def save_gacha_item(self, item_id: str, item_type: str, star_level: int = 1) -> str:
        """Save a gacha item."""
        async with self.get_connection() as conn:
            new_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO gacha_items (id, legacy_id, item_id, type, star_level, obtained_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, new_id, item_id, item_id, item_type, star_level, datetime.now())
            return new_id
    
    async def save_gacha_roll(self, player_id: str, items: List[Dict[str, Any]]) -> str:
        """Save a gacha roll."""
        async with self.get_connection() as conn:
            roll_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO gacha_rolls (id, legacy_id, player_id, items, rolled_at)
                VALUES ($1, $2, $3, $4, $5)
            """, roll_id, roll_id, player_id, json.dumps(items), datetime.now())
            return roll_id
    
    async def get_gacha_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get gacha items."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM gacha_items 
                ORDER BY obtained_at DESC 
                LIMIT $1
            """, limit)
            
            return [
                {
                    "id": row['legacy_id'] or str(row['id']),
                    "item_id": row['item_id'],
                    "type": row['type'],
                    "star_level": row['star_level'],
                    "obtained_at": row['obtained_at'].isoformat() if row['obtained_at'] else None
                }
                for row in rows
            ]
    
    # Upgrade points operations
    async def save_upgrade_points(self, player_id: str, points: int, hp: int = 0, 
                                atk: int = 0, defense: int = 0, crit_rate: int = 0, 
                                crit_damage: int = 0) -> None:
        """Save upgrade points for a player."""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO upgrade_points (player_id, points, hp, atk, def, crit_rate, crit_damage, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (player_id) DO UPDATE SET
                    points = EXCLUDED.points,
                    hp = EXCLUDED.hp,
                    atk = EXCLUDED.atk,
                    def = EXCLUDED.def,
                    crit_rate = EXCLUDED.crit_rate,
                    crit_damage = EXCLUDED.crit_damage,
                    updated_at = EXCLUDED.updated_at
            """, player_id, points, hp, atk, defense, crit_rate, crit_damage, datetime.now())
    
    async def get_upgrade_points(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get upgrade points for a player."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM upgrade_points WHERE player_id = $1",
                player_id
            )
            
            if row:
                return {
                    "player_id": row['player_id'],
                    "points": row['points'],
                    "hp": row['hp'],
                    "atk": row['atk'],
                    "def": row['def'],
                    "crit_rate": row['crit_rate'],
                    "crit_damage": row['crit_damage'],
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                }
            return None
```

### Step 2: Database Configuration

**File**: `backend/autofighter/database/config.py`
```python
"""Database configuration management."""

import os
from typing import Optional

class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self):
        self.host = os.getenv("DATABASE_HOST", "localhost")
        self.port = int(os.getenv("DATABASE_PORT", "5432"))
        self.database = os.getenv("DATABASE_NAME", "autofighter")
        self.username = os.getenv("DATABASE_USER", "autofighter")
        self.password = os.getenv("DATABASE_PASSWORD", "password")
        self.pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.ssl_mode = os.getenv("DATABASE_SSL_MODE", "prefer")
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.ssl_mode}"
        )
    
    def validate(self) -> bool:
        """Validate configuration."""
        required_fields = [self.host, self.database, self.username, self.password]
        return all(field for field in required_fields)

# Global config instance
db_config = DatabaseConfig()
```

### Step 3: Updated SaveManager Interface

**File**: `backend/autofighter/save_manager.py` (replace existing)
```python
"""Save manager with PostgreSQL backend."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from .database.adapter import PostgreSQLAdapter
from .database.config import db_config

logger = logging.getLogger(__name__)

class SaveManager:
    """Save manager with PostgreSQL backend compatibility."""
    
    def __init__(self):
        self.db_adapter: Optional[PostgreSQLAdapter] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection."""
        if self._initialized:
            return
            
        try:
            self.db_adapter = PostgreSQLAdapter(db_config.connection_string, db_config.pool_size)
            await self.db_adapter.initialize()
            self._initialized = True
            logger.info("SaveManager initialized with PostgreSQL backend")
        except Exception as e:
            logger.error(f"Failed to initialize SaveManager: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        if self.db_adapter:
            await self.db_adapter.close()
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure SaveManager is initialized."""
        if not self._initialized:
            raise RuntimeError("SaveManager not initialized. Call initialize() first.")
    
    # Synchronous wrapper methods for backward compatibility
    def save_run(self, run_id: str, party: Dict[str, Any], map_data: Dict[str, Any]) -> str:
        """Save a game run (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.save_run(run_id, party, map_data))
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a game run (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.get_run(run_id))
    
    def list_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List game runs (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.list_runs(limit))
    
    def add_owned_player(self, player_id: str):
        """Add owned player (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.save_owned_player(player_id))
    
    def get_owned_players(self) -> List[str]:
        """Get owned players (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.get_owned_players())
    
    def has_owned_player(self, player_id: str) -> bool:
        """Check if player is owned (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.has_owned_player(player_id))
    
    def save_gacha_roll(self, player_id: str, items: List[Dict[str, Any]]) -> str:
        """Save gacha roll (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.save_gacha_roll(player_id, items))
    
    def get_gacha_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get gacha items (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.get_gacha_items(limit))
    
    def save_upgrade_points(self, player_id: str, points: int, **kwargs):
        """Save upgrade points (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(
            self.db_adapter.save_upgrade_points(player_id, points, **kwargs)
        )
    
    def get_upgrade_points(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get upgrade points (sync wrapper)."""
        self._ensure_initialized()
        return asyncio.create_task(self.db_adapter.get_upgrade_points(player_id))
    
    # Async methods for new code
    async def async_save_run(self, run_id: str, party: Dict[str, Any], map_data: Dict[str, Any]) -> str:
        """Save a game run (async)."""
        self._ensure_initialized()
        return await self.db_adapter.save_run(run_id, party, map_data)
    
    async def async_get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a game run (async)."""
        self._ensure_initialized()
        return await self.db_adapter.get_run(run_id)
    
    async def async_list_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List game runs (async)."""
        self._ensure_initialized()
        return await self.db_adapter.list_runs(limit)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        if not self._initialized:
            return {"healthy": False, "error": "Not initialized"}
        return await self.db_adapter.health_check()

# Global SaveManager instance
save_manager = SaveManager()
```

### Step 4: Backend Integration

**File**: `backend/app.py` (update startup)
```python
"""Updated app.py with PostgreSQL integration."""

from quart import Quart, jsonify
import asyncio
import logging
from autofighter.save_manager import save_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)

@app.before_serving
async def startup():
    """Initialize services on startup."""
    try:
        logger.info("Initializing database connection...")
        await save_manager.initialize()
        logger.info("Backend startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.after_serving
async def shutdown():
    """Cleanup on shutdown."""
    try:
        logger.info("Shutting down database connections...")
        await save_manager.close()
        logger.info("Backend shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

@app.route('/health')
async def health_check():
    """Health check endpoint with database status."""
    try:
        db_health = await save_manager.health_check()
        
        return jsonify({
            "status": "healthy" if db_health["healthy"] else "degraded",
            "service": "autofighter-backend",
            "database": db_health,
            "version": "1.0.0"
        }), 200 if db_health["healthy"] else 503
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "autofighter-backend",
            "error": str(e)
        }), 503

@app.route('/')
async def root():
    """Root endpoint."""
    return jsonify({
        "service": "autofighter-backend",
        "status": "running",
        "version": "1.0.0"
    })

# Include your existing routes here...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=59002, debug=True)
```

### Step 5: Environment Configuration

**File**: `backend/.env.example`
```bash
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=autofighter
DATABASE_USER=autofighter
DATABASE_PASSWORD=password
DATABASE_POOL_SIZE=10
DATABASE_SSL_MODE=prefer

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=59002
DEBUG=True
```

### Step 6: Dependencies Update

**File**: `backend/pyproject.toml` (add dependencies)
```toml
[project]
# ... existing configuration ...

dependencies = [
    # ... existing dependencies ...
    "asyncpg>=0.29.0",
    "python-dotenv>=1.0.0",
]
```

### Step 7: Integration Tests

**File**: `backend/tests/test_database_integration.py`
```python
"""Database integration tests."""

import pytest
import asyncio
import json
from autofighter.database.adapter import PostgreSQLAdapter
from autofighter.database.config import db_config

@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Test PostgreSQL database integration."""
    
    async def setup_class(self):
        """Setup test database adapter."""
        self.adapter = PostgreSQLAdapter(db_config.connection_string)
        await self.adapter.initialize()
    
    async def teardown_class(self):
        """Cleanup test adapter."""
        if self.adapter:
            await self.adapter.close()
    
    async def test_health_check(self):
        """Test database health check."""
        health = await self.adapter.health_check()
        assert health["healthy"] is True
        assert "pool" in health
    
    async def test_save_and_get_run(self):
        """Test saving and retrieving runs."""
        run_id = "test_run_001"
        party = {"player1": {"name": "TestPlayer"}}
        map_data = {"level": 1, "area": "test"}
        
        # Save run
        saved_id = await self.adapter.save_run(run_id, party, map_data)
        assert saved_id is not None
        
        # Get run
        retrieved = await self.adapter.get_run(run_id)
        assert retrieved is not None
        assert retrieved["party"] == party
        assert retrieved["map"] == map_data
    
    async def test_owned_players(self):
        """Test owned players operations."""
        player_id = "test_player_001"
        
        # Add owned player
        saved_id = await self.adapter.save_owned_player(player_id)
        assert saved_id is not None
        
        # Check if owned
        is_owned = await self.adapter.has_owned_player(player_id)
        assert is_owned is True
        
        # Get owned players list
        owned = await self.adapter.get_owned_players()
        assert player_id in owned
    
    async def test_gacha_operations(self):
        """Test gacha operations."""
        # Save gacha item
        item_id = await self.adapter.save_gacha_item("sword_001", "weapon", 3)
        assert item_id is not None
        
        # Save gacha roll
        items = [{"id": "sword_001", "type": "weapon", "star": 3}]
        roll_id = await self.adapter.save_gacha_roll("player_001", items)
        assert roll_id is not None
        
        # Get gacha items
        gacha_items = await self.adapter.get_gacha_items(10)
        assert len(gacha_items) > 0
    
    async def test_upgrade_points(self):
        """Test upgrade points operations."""
        player_id = "player_upgrades_001"
        
        # Save upgrade points
        await self.adapter.save_upgrade_points(
            player_id, points=100, hp=10, atk=5, defense=3
        )
        
        # Get upgrade points
        upgrades = await self.adapter.get_upgrade_points(player_id)
        assert upgrades is not None
        assert upgrades["points"] == 100
        assert upgrades["hp"] == 10
```

## Validation Criteria

### Success Criteria
1. **Database Connection**: Backend successfully connects to PostgreSQL
2. **API Compatibility**: All existing SaveManager methods work unchanged
3. **Data Operations**: CRUD operations function correctly
4. **Connection Pooling**: Database connections are properly pooled
5. **Health Checks**: Database health monitoring works
6. **Error Handling**: Database errors are handled gracefully

### Validation Commands
```bash
# Install new dependencies
cd backend
uv sync

# Set environment variables
cp .env.example .env
# Edit .env with your database settings

# Run integration tests
uv run pytest tests/test_database_integration.py -v

# Test backend health with database
uv run python app.py &
curl http://localhost:59002/health

# Check database connection in pgAdmin
# Navigate to localhost:38085
```

### Expected Results
- Backend starts successfully with PostgreSQL connection
- Health endpoint shows database as healthy
- All database operations complete without errors
- Connection pooling shows proper usage statistics
- SaveManager API remains compatible with existing code

## Notes

- AsyncPG is used for high-performance async PostgreSQL operations
- Connection pooling improves performance and resource management
- Backward compatibility maintained through sync wrapper methods
- Environment variables allow flexible database configuration
- Health checks enable monitoring and debugging database issues