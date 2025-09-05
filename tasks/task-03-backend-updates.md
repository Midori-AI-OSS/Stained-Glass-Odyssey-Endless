# Task 03: Backend Updates for New Architecture

## Objective
Update the backend service to work with the new PostgreSQL database and prepare for router-based communication patterns.

## Requirements

### 1. Database Integration
- Replace `SaveManager` with `PostgreSQLManager` throughout codebase
- Update all database queries to use PostgreSQL syntax
- Maintain existing API functionality
- Add proper error handling for database connections

### 2. API Standardization  
- Consistent response formats across all endpoints
- Proper HTTP status codes
- Standardized error handling
- Request/response logging

### 3. Service Configuration
- Environment-based database configuration
- Health check endpoints
- Graceful shutdown handling
- Service discovery preparation

## Implementation Tasks

### Task 3.1: Update Core Game Module
**File**: `backend/game.py` (Update existing)
```python
# Replace SaveManager imports with PostgreSQL
from autofighter.postgres_manager import PostgreSQLManager

# Update global variables
POSTGRES_MANAGER: PostgreSQLManager | None = None
FERNET: Fernet | None = None

def get_postgres_manager() -> PostgreSQLManager:
    global POSTGRES_MANAGER
    global FERNET

    if POSTGRES_MANAGER is None:
        manager = PostgreSQLManager.from_env()
        manager.migrate(Path(__file__).resolve().parent / "database" / "migrations")
        
        with manager.connection() as conn:
            cursor = conn.cursor()
            
            # Create damage_types table if not exists (PostgreSQL syntax)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS damage_types (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    legacy_id TEXT UNIQUE,
                    type TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Check if we have any owned players
            cursor.execute("SELECT COUNT(*) FROM owned_players")
            count = cursor.fetchone()[0]
            
            if count == 0:
                log.info("No owned players found, adding default player")
                cursor.execute("""
                    INSERT INTO owned_players (legacy_id) 
                    VALUES ('player') 
                    ON CONFLICT (legacy_id) DO NOTHING
                """)
        
        POSTGRES_MANAGER = manager
        
        # Initialize Fernet encryption
        key = os.getenv("AF_DB_KEY", "")
        if key:
            FERNET = Fernet(key.encode() if len(key) == 44 else Fernet.generate_key())
        else:
            FERNET = Fernet(Fernet.generate_key())
            log.warning("No encryption key provided, generated temporary key")

    return POSTGRES_MANAGER

# Update all function calls from get_save_manager() to get_postgres_manager()
# Keep the same function signature for backward compatibility
def get_save_manager() -> PostgreSQLManager:
    """Backward compatibility alias"""
    return get_postgres_manager()
```

### Task 3.2: Update Database Queries
**File**: `backend/query_migration.py`
```python
"""Helper script to update database queries from SQLite to PostgreSQL syntax"""

import re
from pathlib import Path

def update_query_syntax(file_path: Path):
    """Update SQL queries in a Python file to PostgreSQL syntax"""
    
    content = file_path.read_text()
    
    # Common SQLite to PostgreSQL query transformations
    transformations = [
        # Parameter placeholders: ? -> %s
        (r'\?', '%s'),
        
        # AUTOINCREMENT -> SERIAL (for new tables)
        (r'AUTOINCREMENT', 'SERIAL'),
        
        # SQLite functions to PostgreSQL equivalents
        (r'CURRENT_TIMESTAMP', 'NOW()'),
        (r'datetime\(\'now\'\)', 'NOW()'),
        
        # JSON field access (SQLite json_extract -> PostgreSQL ->)
        (r'json_extract\(([^,]+),\s*\'([^\']+)\'\)', r'\1->\'\2\''),
        
        # LIMIT with OFFSET
        (r'LIMIT\s+(\d+)\s+OFFSET\s+(\d+)', r'OFFSET \2 LIMIT \1'),
        
        # Boolean values
        (r'\'true\'', 'TRUE'),
        (r'\'false\'', 'FALSE'),
        
        # INSERT OR IGNORE -> INSERT ... ON CONFLICT DO NOTHING
        (r'INSERT\s+OR\s+IGNORE\s+INTO', 'INSERT INTO'),
        (r'INSERT OR IGNORE INTO', 'INSERT INTO'),
    ]
    
    for pattern, replacement in transformations:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Add ON CONFLICT DO NOTHING for INSERT OR IGNORE patterns
    if 'INSERT INTO' in content and 'ON CONFLICT' not in content:
        # This requires manual review, just add comment
        content = f"# TODO: Review INSERT statements for ON CONFLICT handling\n{content}"
    
    return content

# Update specific query patterns in game.py
def update_game_queries():
    """Update specific database queries in game.py"""
    
    query_updates = {
        # Owned players queries
        'SELECT id FROM owned_players': 'SELECT id, legacy_id FROM owned_players',
        'INSERT INTO owned_players (id) VALUES (?)': 
            'INSERT INTO owned_players (legacy_id) VALUES (%s) ON CONFLICT (legacy_id) DO NOTHING',
        
        # Damage types queries  
        'INSERT INTO damage_types (id, type) VALUES (?, ?)':
            'INSERT INTO damage_types (legacy_id, type) VALUES (%s, %s) ON CONFLICT (legacy_id) DO NOTHING',
        'SELECT type FROM damage_types WHERE id = ?':
            'SELECT type FROM damage_types WHERE legacy_id = %s',
        
        # Run queries
        'INSERT INTO runs (id, party, map) VALUES (?, ?, ?)':
            'INSERT INTO runs (legacy_id, party, map) VALUES (%s, %s::jsonb, %s::jsonb)',
        'SELECT party, map FROM runs WHERE id = ?':
            'SELECT party, map FROM runs WHERE legacy_id = %s',
        'DELETE FROM runs WHERE id = ?':
            'DELETE FROM runs WHERE legacy_id = %s',
    }
    
    return query_updates
```

### Task 3.3: Update Route Handlers
**File**: `backend/routes/players.py` (Update existing)
```python
# Add standardized response format
from datetime import datetime
from typing import Dict, Any

def create_api_response(data: Any = None, message: str = "Success", status: str = "ok") -> Dict:
    """Create standardized API response format"""
    return {
        "status": status,
        "message": message, 
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

def create_error_response(message: str, details: Any = None, status_code: int = 400) -> Dict:
    """Create standardized error response format"""
    return {
        "status": "error",
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }

# Update existing route handlers
@bp.get("/")
async def get_players():
    """Get all owned players with standardized response"""
    try:
        manager = get_postgres_manager()
        with manager.connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM owned_players ORDER BY created_at")
            players = cursor.fetchall()
            
            # Convert to serializable format
            players_data = [dict(player) for player in players]
            
            return create_api_response(
                data={"players": players_data, "count": len(players_data)},
                message=f"Retrieved {len(players_data)} players"
            )
            
    except Exception as e:
        log.exception(f"Error retrieving players: {e}")
        return create_error_response(
            message="Failed to retrieve players",
            details=str(e)
        ), 500

# Apply similar updates to all route handlers
```

### Task 3.4: Add Health Check Endpoints
**File**: `backend/routes/health.py` (New file)
```python
"""Health check endpoints for backend service"""

from quart import Blueprint, jsonify
from datetime import datetime
import psycopg2
import logging

from game import get_postgres_manager

log = logging.getLogger(__name__)
bp = Blueprint("health", __name__)

@bp.get("/")
async def health_check():
    """Comprehensive health check"""
    
    health_status = {
        "service": "midori-autofighter-backend",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database connectivity check
    try:
        manager = get_postgres_manager()
        with manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                health_status["checks"]["database"] = {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
            else:
                health_status["checks"]["database"] = {
                    "status": "unhealthy", 
                    "message": "Database query failed"
                }
                health_status["status"] = "unhealthy"
                
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {e}"
        }
        health_status["status"] = "unhealthy"
    
    # Service dependencies check
    health_status["checks"]["dependencies"] = {
        "status": "healthy",
        "torch_available": is_torch_available(),
        "encryption_available": bool(os.getenv("AF_DB_KEY"))
    }
    
    # Determine overall status
    if health_status["status"] == "healthy":
        return jsonify(health_status), 200
    else:
        return jsonify(health_status), 503

@bp.get("/ready")
async def readiness_check():
    """Readiness probe for Kubernetes/Docker"""
    try:
        manager = get_postgres_manager()
        with manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM owned_players")
            count = cursor.fetchone()[0]
            
            return jsonify({
                "status": "ready",
                "database": "connected",
                "players_count": count,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
    except Exception as e:
        return jsonify({
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

@bp.get("/live")
async def liveness_check():
    """Liveness probe for Kubernetes/Docker"""
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }), 200
```

### Task 3.5: Update Main Application
**File**: `backend/app.py` (Update existing)
```python
# Add health routes
from routes.health import bp as health_bp

# Register health blueprint
app.register_blueprint(health_bp, url_prefix='/health')

# Update status endpoint with more details
@app.get("/")
async def status() -> Response:
    """Enhanced status endpoint"""
    try:
        # Check database connection
        manager = get_postgres_manager()
        with manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM owned_players")
            player_count = cursor.fetchone()[0]
            
        return jsonify({
            "status": "ok", 
            "flavor": BACKEND_FLAVOR,
            "service": "midori-autofighter-backend",
            "version": "2.0.0",
            "database": "connected",
            "players": player_count,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        log.exception(f"Status check failed: {e}")
        return jsonify({
            "status": "degraded",
            "flavor": BACKEND_FLAVOR, 
            "service": "midori-autofighter-backend",
            "version": "2.0.0",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

# Add graceful shutdown handling
import signal
import asyncio

async def shutdown_handler():
    """Handle graceful shutdown"""
    log.info("Shutting down backend service...")
    
    # Close database connections
    global POSTGRES_MANAGER
    if POSTGRES_MANAGER:
        # PostgreSQL connections are handled per-request, no global cleanup needed
        log.info("Database connections will be closed automatically")
    
    log.info("Backend service shutdown complete")

# Register shutdown handler
@app.before_serving
async def startup():
    log.info("Starting backend service...")
    
    # Initialize database connection
    try:
        manager = get_postgres_manager()
        log.info("Database connection initialized successfully")
    except Exception as e:
        log.error(f"Failed to initialize database: {e}")
        raise

@app.after_serving
async def shutdown():
    await shutdown_handler()
```

### Task 3.6: Environment Configuration
**File**: `backend/.env.example` (Update existing)
```env
# Database Configuration
DATABASE_URL=postgresql://autofighter:password@database:5432/autofighter
AF_DB_KEY=your-encryption-key-here

# Service Configuration  
BACKEND_HOST=0.0.0.0
BACKEND_PORT=59002
LOG_LEVEL=INFO

# Feature Flags
UV_EXTRA=default
ENABLE_LLM=false

# Router Communication
ROUTER_HOST=router
ROUTER_PORT=59000

# Development Settings
DEBUG=false
RELOAD=false
```

### Task 3.7: Dependencies Update
**File**: `backend/pyproject.toml` (Add PostgreSQL dependencies)
```toml
[project.optional-dependencies]
postgresql = [
    "psycopg2-binary>=2.9.0",
    "SQLAlchemy>=2.0.0",  # For potential future ORM migration
]

# Update existing dependencies
dependencies = [
    # ... existing dependencies ...
    "psycopg2-binary>=2.9.0",
]
```

### Task 3.8: Migration Validation Script
**File**: `backend/validate_backend_migration.py`
```python
#!/usr/bin/env python3
"""Validate backend migration to PostgreSQL"""

import asyncio
import httpx
import psycopg2
import os
import sys
from pathlib import Path

async def validate_backend():
    """Validate backend service after migration"""
    
    print("🔍 Validating backend migration...")
    
    # Test database connection
    print("  📋 Testing database connection...")
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://autofighter:password@localhost:5432/autofighter")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result[0] == 1:
            print("    ✓ Database connection successful")
        else:
            print("    ❌ Database connection failed")
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"    ❌ Database connection error: {e}")
        return False
    
    # Test backend API endpoints
    print("  🌐 Testing API endpoints...")
    base_url = "http://localhost:59002"
    
    try:
        async with httpx.AsyncClient() as client:
            # Test status endpoint
            response = await client.get(f"{base_url}/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["ok", "degraded"]
            print("    ✓ Status endpoint working")
            
            # Test health endpoint
            response = await client.get(f"{base_url}/health/")
            assert response.status_code in [200, 503]
            print("    ✓ Health endpoint working")
            
            # Test players endpoint
            response = await client.get(f"{base_url}/players")
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            print("    ✓ Players endpoint working")
            
            # Test gacha endpoint
            response = await client.get(f"{base_url}/gacha")
            assert response.status_code == 200
            print("    ✓ Gacha endpoint working")
            
    except Exception as e:
        print(f"    ❌ API endpoint test failed: {e}")
        return False
    
    print("✅ Backend migration validation passed!")
    return True

if __name__ == "__main__":
    result = asyncio.run(validate_backend())
    sys.exit(0 if result else 1)
```

### Task 3.9: Update Route Files
Update all route files (`routes/*.py`) with the following changes:

1. **Import PostgreSQL manager**:
   ```python
   from game import get_postgres_manager
   import psycopg2.extras
   ```

2. **Use cursor pattern**:
   ```python
   # OLD:
   with manager.connection() as conn:
       conn.execute(query, params)
       result = conn.fetchone()
   
   # NEW:
   with manager.connection() as conn:
       cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
       cursor.execute(query, params)
       result = cursor.fetchone()
   ```

3. **Update query parameters**:
   ```python
   # OLD: SQLite style
   cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
   
   # NEW: PostgreSQL style  
   cursor.execute("SELECT * FROM players WHERE legacy_id = %s", (player_id,))
   ```

4. **Add response standardization**:
   ```python
   from routes.players import create_api_response, create_error_response
   ```

## Testing Commands

```bash
# Install PostgreSQL dependencies
cd backend
uv sync --extra postgresql

# Start database services
cd ../database
docker-compose -f docker-compose.database.yml up -d

# Run migration if not done
python migrate_from_sqlite.py

# Start backend service
cd ../backend
uv run app.py

# Run validation
python validate_backend_migration.py

# Test endpoints
curl http://localhost:59002/
curl http://localhost:59002/health/
curl http://localhost:59002/players
```

## Completion Criteria

- [ ] PostgreSQL manager replaces SaveManager throughout codebase
- [ ] All database queries updated to PostgreSQL syntax
- [ ] Health check endpoints implemented and working
- [ ] Standardized API response format across all endpoints
- [ ] Environment-based configuration working
- [ ] Graceful startup and shutdown handling
- [ ] Backend validation script passes all tests
- [ ] All existing functionality preserved

## Notes for Task Master Review

- Database queries maintain backward compatibility where possible
- Health checks enable monitoring and debugging
- Standardized responses improve API consistency  
- Environment configuration supports different deployment scenarios
- Graceful shutdown prevents data corruption

**Next Task**: After completion and review, proceed to `task-04-frontend-simplification.md`