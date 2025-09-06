# Task 3A: Backend Database Integration

## Overview

This task replaces the existing SaveManager system with the new PostgreSQL integration, updating all backend code to use the new database adapter while maintaining API compatibility.

## Goals

- Replace SQLite SaveManager usage with PostgreSQL adapter
- Update game logic to use async database operations
- Maintain existing API endpoints and responses
- Add proper error handling and logging
- Implement database transaction support

## Prerequisites

- Task 2A (Database Setup) must be completed
- Task 2B (Database Migration) must be completed  
- Task 2C (Database Integration) must be completed
- Backend service structure in place

## Implementation

### Step 1: Update Game Logic

**File**: `backend/autofighter/game.py` (update existing)
```python
"""Updated game logic with PostgreSQL integration."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from .save_manager import save_manager
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class GameSession:
    """Game session with PostgreSQL persistence."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.party: Dict[str, Any] = {}
        self.map_data: Dict[str, Any] = {}
        self.current_run_id: Optional[str] = None
        
    async def start_new_run(self, party_config: Dict[str, Any], map_config: Dict[str, Any]) -> str:
        """Start a new game run with persistence."""
        try:
            self.current_run_id = str(uuid.uuid4())
            self.party = party_config
            self.map_data = map_config
            
            # Save run to database
            await save_manager.async_save_run(self.current_run_id, party_config, map_config)
            
            logger.info(f"Started new run: {self.current_run_id}")
            return self.current_run_id
            
        except Exception as e:
            logger.error(f"Failed to start new run: {e}")
            raise
    
    async def save_run_state(self) -> bool:
        """Save current run state to database."""
        if not self.current_run_id:
            return False
            
        try:
            await save_manager.async_save_run(self.current_run_id, self.party, self.map_data)
            logger.debug(f"Saved run state: {self.current_run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save run state: {e}")
            return False
    
    async def load_run(self, run_id: str) -> bool:
        """Load existing run from database."""
        try:
            run_data = await save_manager.async_get_run(run_id)
            if run_data:
                self.current_run_id = run_id
                self.party = run_data.get("party", {})
                self.map_data = run_data.get("map", {})
                logger.info(f"Loaded run: {run_id}")
                return True
            else:
                logger.warning(f"Run not found: {run_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load run: {e}")
            return False
    
    async def add_owned_player(self, player_id: str, player_data: Dict[str, Any] = None) -> bool:
        """Add a player to owned collection."""
        try:
            await save_manager.db_adapter.save_owned_player(player_id, player_data)
            logger.info(f"Added owned player: {player_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add owned player: {e}")
            return False
    
    async def get_owned_players(self) -> List[str]:
        """Get list of owned players."""
        try:
            return await save_manager.db_adapter.get_owned_players()
        except Exception as e:
            logger.error(f"Failed to get owned players: {e}")
            return []
    
    async def perform_gacha_roll(self, player_id: str, roll_type: str = "standard") -> Dict[str, Any]:
        """Perform gacha roll with persistence."""
        try:
            # Simulate gacha logic (replace with actual implementation)
            items = await self._simulate_gacha_roll(roll_type)
            
            # Save roll to database
            roll_id = await save_manager.db_adapter.save_gacha_roll(player_id, items)
            
            # Save individual items
            for item in items:
                await save_manager.db_adapter.save_gacha_item(
                    item["id"], item["type"], item.get("star_level", 1)
                )
            
            logger.info(f"Gacha roll completed: {roll_id} ({len(items)} items)")
            return {
                "roll_id": roll_id,
                "items": items,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Gacha roll failed: {e}")
            raise
    
    async def _simulate_gacha_roll(self, roll_type: str) -> List[Dict[str, Any]]:
        """Simulate gacha roll logic."""
        # This is a placeholder - implement actual gacha logic
        import random
        
        items = []
        num_items = random.randint(1, 5)
        
        for i in range(num_items):
            item = {
                "id": f"item_{uuid.uuid4().hex[:8]}",
                "type": random.choice(["weapon", "armor", "character"]),
                "star_level": random.randint(1, 5),
                "name": f"Random Item {i+1}"
            }
            items.append(item)
        
        return items
    
    async def update_upgrade_points(self, player_id: str, points_delta: int, 
                                   stat_upgrades: Dict[str, int] = None) -> Dict[str, Any]:
        """Update player upgrade points."""
        try:
            # Get current upgrade points
            current = await save_manager.db_adapter.get_upgrade_points(player_id)
            
            if current:
                new_points = current["points"] + points_delta
                new_stats = {
                    "hp": current["hp"] + stat_upgrades.get("hp", 0),
                    "atk": current["atk"] + stat_upgrades.get("atk", 0),
                    "def": current["def"] + stat_upgrades.get("def", 0),
                    "crit_rate": current["crit_rate"] + stat_upgrades.get("crit_rate", 0),
                    "crit_damage": current["crit_damage"] + stat_upgrades.get("crit_damage", 0)
                }
            else:
                new_points = points_delta
                new_stats = stat_upgrades or {}
            
            # Save updated points
            await save_manager.db_adapter.save_upgrade_points(
                player_id, new_points, **new_stats
            )
            
            result = {"player_id": player_id, "points": new_points, **new_stats}
            logger.info(f"Updated upgrade points for {player_id}: {new_points} points")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update upgrade points: {e}")
            raise

class GameManager:
    """Global game manager with session handling."""
    
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        
    async def create_session(self, session_id: str = None) -> GameSession:
        """Create new game session."""
        session = GameSession(session_id)
        self.sessions[session.session_id] = session
        logger.info(f"Created game session: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[GameSession]:
        """Get existing game session."""
        return self.sessions.get(session_id)
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Cleanup game session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Save final state
            await session.save_run_state()
            del self.sessions[session_id]
            logger.info(f"Cleaned up session: {session_id}")
            return True
        return False
    
    async def list_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent game runs."""
        try:
            return await save_manager.async_list_runs(limit)
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []

# Global game manager instance
game_manager = GameManager()
```

### Step 2: Update API Routes

**File**: `backend/routes/game_routes.py` (create new)
```python
"""Game API routes with PostgreSQL integration."""

from quart import Blueprint, request, jsonify
from autofighter.game import game_manager
from autofighter.save_manager import save_manager
import logging

logger = logging.getLogger(__name__)
game_bp = Blueprint('game', __name__, url_prefix='/api/game')

@game_bp.route('/session', methods=['POST'])
async def create_session():
    """Create new game session."""
    try:
        data = await request.get_json() or {}
        session_id = data.get('session_id')
        
        session = await game_manager.create_session(session_id)
        
        return jsonify({
            "session_id": session.session_id,
            "status": "created"
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/session/<session_id>/run', methods=['POST'])
async def start_run(session_id: str):
    """Start new game run."""
    try:
        session = game_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        data = await request.get_json()
        party = data.get('party', {})
        map_config = data.get('map', {})
        
        run_id = await session.start_new_run(party, map_config)
        
        return jsonify({
            "run_id": run_id,
            "session_id": session_id,
            "status": "started"
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to start run: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/session/<session_id>/run/<run_id>', methods=['GET'])
async def get_run(session_id: str, run_id: str):
    """Get game run details."""
    try:
        run_data = await save_manager.async_get_run(run_id)
        if not run_data:
            return jsonify({"error": "Run not found"}), 404
        
        return jsonify(run_data), 200
        
    except Exception as e:
        logger.error(f"Failed to get run: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/runs', methods=['GET'])
async def list_runs():
    """List recent game runs."""
    try:
        limit = int(request.args.get('limit', 10))
        runs = await game_manager.list_recent_runs(limit)
        
        return jsonify({
            "runs": runs,
            "count": len(runs)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/players/owned', methods=['GET'])
async def get_owned_players():
    """Get owned players list."""
    try:
        players = await save_manager.db_adapter.get_owned_players()
        
        return jsonify({
            "players": players,
            "count": len(players)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get owned players: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/players/<player_id>/own', methods=['POST'])
async def add_owned_player(player_id: str):
    """Add player to owned collection."""
    try:
        data = await request.get_json() or {}
        player_data = data.get('player_data')
        
        await save_manager.db_adapter.save_owned_player(player_id, player_data)
        
        return jsonify({
            "player_id": player_id,
            "status": "added"
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to add owned player: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/gacha/roll', methods=['POST'])
async def gacha_roll():
    """Perform gacha roll."""
    try:
        data = await request.get_json()
        player_id = data.get('player_id', 'default')
        roll_type = data.get('type', 'standard')
        
        # Create temporary session for gacha
        session = await game_manager.create_session()
        result = await session.perform_gacha_roll(player_id, roll_type)
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Gacha roll failed: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/gacha/items', methods=['GET'])
async def get_gacha_items():
    """Get gacha items."""
    try:
        limit = int(request.args.get('limit', 50))
        items = await save_manager.db_adapter.get_gacha_items(limit)
        
        return jsonify({
            "items": items,
            "count": len(items)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get gacha items: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/players/<player_id>/upgrades', methods=['GET'])
async def get_upgrade_points(player_id: str):
    """Get player upgrade points."""
    try:
        upgrades = await save_manager.db_adapter.get_upgrade_points(player_id)
        
        if upgrades:
            return jsonify(upgrades), 200
        else:
            return jsonify({
                "player_id": player_id,
                "points": 0,
                "hp": 0, "atk": 0, "def": 0,
                "crit_rate": 0, "crit_damage": 0
            }), 200
        
    except Exception as e:
        logger.error(f"Failed to get upgrade points: {e}")
        return jsonify({"error": str(e)}), 500

@game_bp.route('/players/<player_id>/upgrades', methods=['POST'])
async def update_upgrades(player_id: str):
    """Update player upgrade points."""
    try:
        data = await request.get_json()
        points_delta = data.get('points_delta', 0)
        stat_upgrades = data.get('stat_upgrades', {})
        
        session = await game_manager.create_session()
        result = await session.update_upgrade_points(player_id, points_delta, stat_upgrades)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to update upgrades: {e}")
        return jsonify({"error": str(e)}), 500
```

### Step 3: Update Main Application

**File**: `backend/app.py` (update routes registration)
```python
"""Updated app.py with new route registration."""

from quart import Quart, jsonify
import asyncio
import logging
from autofighter.save_manager import save_manager
from routes.game_routes import game_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)

# Register blueprints
app.register_blueprint(game_bp)

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
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "game_api": "/api/game",
            "documentation": "/docs"
        }
    })

@app.route('/api/')
async def api_root():
    """API root endpoint for router compatibility."""
    return jsonify({
        "flavor": "default",
        "status": "ok",
        "database_connected": (await save_manager.health_check())["healthy"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=59002, debug=True)
```

### Step 4: Error Handling and Logging

**File**: `backend/autofighter/exceptions.py` (create new)
```python
"""Custom exceptions for game logic."""

class GameException(Exception):
    """Base exception for game-related errors."""
    pass

class DatabaseException(GameException):
    """Database operation errors."""
    pass

class SessionException(GameException):
    """Game session errors."""
    pass

class ValidationException(GameException):
    """Data validation errors."""
    pass
```

**File**: `backend/autofighter/middleware.py` (create new)
```python
"""Middleware for error handling and logging."""

from quart import jsonify
import logging
from .exceptions import GameException, DatabaseException

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(DatabaseException)
    async def handle_database_error(error):
        logger.error(f"Database error: {error}")
        return jsonify({
            "error": "Database operation failed",
            "message": str(error),
            "type": "database_error"
        }), 500
    
    @app.errorhandler(GameException)
    async def handle_game_error(error):
        logger.error(f"Game error: {error}")
        return jsonify({
            "error": "Game operation failed",
            "message": str(error),
            "type": "game_error"
        }), 400
    
    @app.errorhandler(Exception)
    async def handle_generic_error(error):
        logger.exception(f"Unhandled error: {error}")
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "type": "internal_error"
        }), 500
```

### Step 5: Integration Tests

**File**: `backend/tests/test_game_integration.py`
```python
"""Integration tests for game logic with PostgreSQL."""

import pytest
import asyncio
from autofighter.game import GameManager, GameSession
from autofighter.save_manager import save_manager

@pytest.mark.asyncio
class TestGameIntegration:
    """Test game logic with PostgreSQL integration."""
    
    async def setup_class(self):
        """Setup test environment."""
        await save_manager.initialize()
        self.game_manager = GameManager()
    
    async def teardown_class(self):
        """Cleanup test environment."""
        await save_manager.close()
    
    async def test_create_session(self):
        """Test game session creation."""
        session = await self.game_manager.create_session()
        assert session is not None
        assert session.session_id is not None
        
        # Should be able to retrieve session
        retrieved = self.game_manager.get_session(session.session_id)
        assert retrieved is session
    
    async def test_start_and_load_run(self):
        """Test starting and loading game runs."""
        session = await self.game_manager.create_session()
        
        party = {"player1": {"name": "TestPlayer", "level": 1}}
        map_data = {"level": 1, "area": "test_area"}
        
        # Start new run
        run_id = await session.start_new_run(party, map_data)
        assert run_id is not None
        
        # Load run in new session
        new_session = await self.game_manager.create_session()
        loaded = await new_session.load_run(run_id)
        assert loaded is True
        assert new_session.party == party
        assert new_session.map_data == map_data
    
    async def test_owned_players(self):
        """Test owned players management."""
        session = await self.game_manager.create_session()
        
        player_id = "test_player_integration"
        player_data = {"name": "Test Player", "class": "warrior"}
        
        # Add owned player
        success = await session.add_owned_player(player_id, player_data)
        assert success is True
        
        # Get owned players
        owned = await session.get_owned_players()
        assert player_id in owned
    
    async def test_gacha_system(self):
        """Test gacha roll system."""
        session = await self.game_manager.create_session()
        
        player_id = "test_gacha_player"
        result = await session.perform_gacha_roll(player_id, "standard")
        
        assert "roll_id" in result
        assert "items" in result
        assert len(result["items"]) > 0
        
        # Verify items were saved
        gacha_items = await save_manager.db_adapter.get_gacha_items(10)
        assert len(gacha_items) > 0
    
    async def test_upgrade_points(self):
        """Test upgrade points system."""
        session = await self.game_manager.create_session()
        
        player_id = "test_upgrade_player"
        
        # Add initial points
        result = await session.update_upgrade_points(
            player_id, 100, {"hp": 10, "atk": 5}
        )
        assert result["points"] == 100
        assert result["hp"] == 10
        assert result["atk"] == 5
        
        # Add more points
        result = await session.update_upgrade_points(
            player_id, 50, {"def": 3}
        )
        assert result["points"] == 150
        assert result["hp"] == 10  # Should preserve previous
        assert result["def"] == 3
    
    async def test_session_cleanup(self):
        """Test session cleanup."""
        session = await self.game_manager.create_session()
        session_id = session.session_id
        
        # Start a run to have state to save
        await session.start_new_run({"test": "data"}, {"test": "map"})
        
        # Cleanup session
        cleaned = await self.game_manager.cleanup_session(session_id)
        assert cleaned is True
        
        # Session should be removed
        retrieved = self.game_manager.get_session(session_id)
        assert retrieved is None
```

## Validation Criteria

### Success Criteria
1. **API Compatibility**: All existing endpoints work with new database
2. **Game Logic**: Game sessions, runs, and state management function correctly
3. **Data Persistence**: All game data is properly saved to PostgreSQL
4. **Error Handling**: Database errors are caught and handled gracefully
5. **Performance**: Database operations complete within acceptable timeframes

### Validation Commands
```bash
# Install dependencies and run tests
cd backend
uv sync
uv run pytest tests/test_game_integration.py -v

# Test API endpoints
uv run python app.py &

# Create session
curl -X POST http://localhost:59002/api/game/session

# Start run
curl -X POST http://localhost:59002/api/game/session/{session_id}/run \
  -H "Content-Type: application/json" \
  -d '{"party": {"player1": {"name": "Test"}}, "map": {"level": 1}}'

# Test gacha
curl -X POST http://localhost:59002/api/game/gacha/roll \
  -H "Content-Type: application/json" \
  -d '{"player_id": "test", "type": "standard"}'
```

### Expected Results
- Backend starts successfully with PostgreSQL connection
- All API endpoints respond correctly
- Game sessions can be created and managed
- Runs are saved and loaded from database
- Gacha system generates and persists items
- Upgrade points are tracked correctly
- Error handling prevents crashes

## Notes

- Async/await patterns used throughout for database operations
- Session management allows multiple concurrent games
- Error handling provides detailed information for debugging
- API maintains backward compatibility while adding new features
- PostgreSQL provides better performance and concurrent access than SQLite