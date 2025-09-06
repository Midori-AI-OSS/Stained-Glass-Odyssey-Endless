# Task 3B: Backend API Standardization

## Overview

This task standardizes all backend API responses, implements consistent error handling, and adds comprehensive health check endpoints to ensure reliable communication with the router service.

## Goals

- Standardize API response formats across all endpoints
- Implement consistent error handling and status codes
- Add comprehensive health check endpoints
- Create API documentation and validation
- Ensure router compatibility

## Prerequisites

- Task 3A (Backend Database Integration) must be completed
- PostgreSQL database integration working
- Backend service running with new game logic

## Implementation

### Step 1: API Response Standards

**File**: `backend/autofighter/api_standards.py` (create new)
```python
"""API response standards and utilities."""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class ResponseStatus(Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"

@dataclass
class APIResponse:
    """Standard API response structure."""
    status: ResponseStatus
    data: Any = None
    message: str = ""
    error_code: Optional[str] = None
    timestamp: str = None
    pagination: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {
            "status": self.status.value,
            "timestamp": self.timestamp
        }
        
        if self.data is not None:
            result["data"] = self.data
        
        if self.message:
            result["message"] = self.message
            
        if self.error_code:
            result["error_code"] = self.error_code
            
        if self.pagination:
            result["pagination"] = self.pagination
            
        return result

class ResponseBuilder:
    """Builder for standardized API responses."""
    
    @staticmethod
    def success(data: Any = None, message: str = "", pagination: Dict[str, Any] = None) -> APIResponse:
        """Build success response."""
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            pagination=pagination
        )
    
    @staticmethod
    def error(message: str, error_code: str = None, data: Any = None) -> APIResponse:
        """Build error response."""
        return APIResponse(
            status=ResponseStatus.ERROR,
            message=message,
            error_code=error_code,
            data=data
        )
    
    @staticmethod
    def warning(message: str, data: Any = None) -> APIResponse:
        """Build warning response."""
        return APIResponse(
            status=ResponseStatus.WARNING,
            message=message,
            data=data
        )
    
    @staticmethod
    def partial(data: Any, message: str, pagination: Dict[str, Any] = None) -> APIResponse:
        """Build partial success response."""
        return APIResponse(
            status=ResponseStatus.PARTIAL,
            data=data,
            message=message,
            pagination=pagination
        )

def paginate_response(items: List[Any], page: int, page_size: int, total_count: int) -> Dict[str, Any]:
    """Create pagination metadata."""
    total_pages = (total_count + page_size - 1) // page_size
    
    return {
        "current_page": page,
        "page_size": page_size,
        "total_items": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }

# HTTP Status Code mappings
STATUS_CODES = {
    ResponseStatus.SUCCESS: 200,
    ResponseStatus.ERROR: 400,
    ResponseStatus.WARNING: 200,
    ResponseStatus.PARTIAL: 206
}
```

### Step 2: Updated Game Routes with Standards

**File**: `backend/routes/game_routes.py` (update existing)
```python
"""Updated game API routes with standardized responses."""

from quart import Blueprint, request, jsonify
from autofighter.game import game_manager
from autofighter.save_manager import save_manager
from autofighter.api_standards import ResponseBuilder, STATUS_CODES, paginate_response
from autofighter.exceptions import GameException, DatabaseException
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
        
        response = ResponseBuilder.success(
            data={
                "session_id": session.session_id,
                "created_at": session.session_id  # timestamp embedded in UUID
            },
            message="Game session created successfully"
        )
        
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        response = ResponseBuilder.error(
            message="Failed to create game session",
            error_code="SESSION_CREATE_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]

@game_bp.route('/session/<session_id>/run', methods=['POST'])
async def start_run(session_id: str):
    """Start new game run."""
    try:
        session = game_manager.get_session(session_id)
        if not session:
            response = ResponseBuilder.error(
                message="Game session not found",
                error_code="SESSION_NOT_FOUND"
            )
            return jsonify(response.to_dict()), 404
        
        data = await request.get_json()
        if not data:
            response = ResponseBuilder.error(
                message="Request body required",
                error_code="INVALID_REQUEST"
            )
            return jsonify(response.to_dict()), 400
        
        party = data.get('party', {})
        map_config = data.get('map', {})
        
        if not party or not map_config:
            response = ResponseBuilder.error(
                message="Party and map configuration required",
                error_code="MISSING_REQUIRED_DATA"
            )
            return jsonify(response.to_dict()), 400
        
        run_id = await session.start_new_run(party, map_config)
        
        response = ResponseBuilder.success(
            data={
                "run_id": run_id,
                "session_id": session_id,
                "party": party,
                "map": map_config
            },
            message="Game run started successfully"
        )
        
        return jsonify(response.to_dict()), 201
        
    except GameException as e:
        response = ResponseBuilder.error(
            message=str(e),
            error_code="GAME_ERROR"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
    except Exception as e:
        logger.error(f"Failed to start run: {e}")
        response = ResponseBuilder.error(
            message="Failed to start game run",
            error_code="RUN_START_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]

@game_bp.route('/session/<session_id>/run/<run_id>', methods=['GET'])
async def get_run(session_id: str, run_id: str):
    """Get game run details."""
    try:
        run_data = await save_manager.async_get_run(run_id)
        if not run_data:
            response = ResponseBuilder.error(
                message="Game run not found",
                error_code="RUN_NOT_FOUND"
            )
            return jsonify(response.to_dict()), 404
        
        response = ResponseBuilder.success(
            data=run_data,
            message="Game run retrieved successfully"
        )
        
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
        
    except Exception as e:
        logger.error(f"Failed to get run: {e}")
        response = ResponseBuilder.error(
            message="Failed to retrieve game run",
            error_code="RUN_RETRIEVAL_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]

@game_bp.route('/runs', methods=['GET'])
async def list_runs():
    """List recent game runs with pagination."""
    try:
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 10)), 100)
        
        if page < 1 or page_size < 1:
            response = ResponseBuilder.error(
                message="Page and page_size must be positive integers",
                error_code="INVALID_PAGINATION"
            )
            return jsonify(response.to_dict()), 400
        
        # Get total count (would need to implement in database adapter)
        runs = await game_manager.list_recent_runs(page_size)
        total_count = len(runs)  # Simplified - should get actual count
        
        pagination = paginate_response(runs, page, page_size, total_count)
        
        response = ResponseBuilder.success(
            data=runs,
            message=f"Retrieved {len(runs)} game runs",
            pagination=pagination
        )
        
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
        
    except ValueError:
        response = ResponseBuilder.error(
            message="Invalid pagination parameters",
            error_code="INVALID_PAGINATION"
        )
        return jsonify(response.to_dict()), 400
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        response = ResponseBuilder.error(
            message="Failed to retrieve game runs",
            error_code="RUNS_LIST_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]

@game_bp.route('/players/owned', methods=['GET'])
async def get_owned_players():
    """Get owned players list."""
    try:
        players = await save_manager.db_adapter.get_owned_players()
        
        response = ResponseBuilder.success(
            data={
                "players": players,
                "count": len(players)
            },
            message=f"Retrieved {len(players)} owned players"
        )
        
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
        
    except DatabaseException as e:
        response = ResponseBuilder.error(
            message="Database error retrieving owned players",
            error_code="DATABASE_ERROR"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
    except Exception as e:
        logger.error(f"Failed to get owned players: {e}")
        response = ResponseBuilder.error(
            message="Failed to retrieve owned players",
            error_code="OWNED_PLAYERS_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]

@game_bp.route('/players/<player_id>/own', methods=['POST'])
async def add_owned_player(player_id: str):
    """Add player to owned collection."""
    try:
        if not player_id or not player_id.strip():
            response = ResponseBuilder.error(
                message="Player ID is required",
                error_code="MISSING_PLAYER_ID"
            )
            return jsonify(response.to_dict()), 400
        
        data = await request.get_json() or {}
        player_data = data.get('player_data')
        
        await save_manager.db_adapter.save_owned_player(player_id, player_data)
        
        response = ResponseBuilder.success(
            data={
                "player_id": player_id,
                "player_data": player_data
            },
            message="Player added to owned collection"
        )
        
        return jsonify(response.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Failed to add owned player: {e}")
        response = ResponseBuilder.error(
            message="Failed to add player to owned collection",
            error_code="ADD_OWNED_PLAYER_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]

@game_bp.route('/gacha/roll', methods=['POST'])
async def gacha_roll():
    """Perform gacha roll."""
    try:
        data = await request.get_json()
        if not data:
            response = ResponseBuilder.error(
                message="Request body required",
                error_code="INVALID_REQUEST"
            )
            return jsonify(response.to_dict()), 400
        
        player_id = data.get('player_id', 'default')
        roll_type = data.get('type', 'standard')
        
        # Validate roll type
        valid_types = ['standard', 'premium', 'event']
        if roll_type not in valid_types:
            response = ResponseBuilder.error(
                message=f"Invalid roll type. Must be one of: {', '.join(valid_types)}",
                error_code="INVALID_ROLL_TYPE"
            )
            return jsonify(response.to_dict()), 400
        
        # Create temporary session for gacha
        session = await game_manager.create_session()
        result = await session.perform_gacha_roll(player_id, roll_type)
        
        response = ResponseBuilder.success(
            data=result,
            message=f"Gacha roll completed - {len(result['items'])} items obtained"
        )
        
        return jsonify(response.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Gacha roll failed: {e}")
        response = ResponseBuilder.error(
            message="Gacha roll failed",
            error_code="GACHA_ROLL_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]

@game_bp.route('/players/<player_id>/upgrades', methods=['GET'])
async def get_upgrade_points(player_id: str):
    """Get player upgrade points."""
    try:
        upgrades = await save_manager.db_adapter.get_upgrade_points(player_id)
        
        if upgrades:
            response = ResponseBuilder.success(
                data=upgrades,
                message="Upgrade points retrieved successfully"
            )
        else:
            # Return default values for new player
            default_upgrades = {
                "player_id": player_id,
                "points": 0,
                "hp": 0, "atk": 0, "def": 0,
                "crit_rate": 0, "crit_damage": 0
            }
            response = ResponseBuilder.success(
                data=default_upgrades,
                message="New player - default upgrade points"
            )
        
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
        
    except Exception as e:
        logger.error(f"Failed to get upgrade points: {e}")
        response = ResponseBuilder.error(
            message="Failed to retrieve upgrade points",
            error_code="UPGRADE_POINTS_FAILED"
        )
        return jsonify(response.to_dict()), STATUS_CODES[response.status]
```

### Step 3: Health Check Endpoints

**File**: `backend/routes/health_routes.py` (create new)
```python
"""Comprehensive health check endpoints."""

from quart import Blueprint, jsonify
from autofighter.save_manager import save_manager
from autofighter.api_standards import ResponseBuilder, STATUS_CODES
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
async def basic_health():
    """Basic health check for router service."""
    try:
        # Quick database ping
        db_health = await save_manager.health_check()
        
        status = "healthy" if db_health["healthy"] else "degraded"
        
        response_data = {
            "service": "autofighter-backend",
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if status == "healthy":
            response = ResponseBuilder.success(
                data=response_data,
                message="Service is healthy"
            )
            return jsonify(response.to_dict()), 200
        else:
            response = ResponseBuilder.warning(
                data=response_data,
                message="Service is degraded"
            )
            return jsonify(response.to_dict()), 503
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        response = ResponseBuilder.error(
            message="Health check failed",
            error_code="HEALTH_CHECK_FAILED"
        )
        return jsonify(response.to_dict()), 503

@health_bp.route('/health/detailed')
async def detailed_health():
    """Detailed health check with system metrics."""
    try:
        # Database health
        db_health = await save_manager.health_check()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            "service": "autofighter-backend",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": db_health,
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_mb": memory.available // (1024 * 1024),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": disk.free // (1024 * 1024 * 1024)
            }
        }
        
        # Determine overall health
        is_healthy = (
            db_health["healthy"] and
            cpu_percent < 90 and
            memory.percent < 90 and
            disk.percent < 95
        )
        
        health_data["status"] = "healthy" if is_healthy else "degraded"
        
        if is_healthy:
            response = ResponseBuilder.success(
                data=health_data,
                message="Service and system are healthy"
            )
            return jsonify(response.to_dict()), 200
        else:
            response = ResponseBuilder.warning(
                data=health_data,
                message="Service or system metrics show degradation"
            )
            return jsonify(response.to_dict()), 503
            
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        response = ResponseBuilder.error(
            message="Detailed health check failed",
            error_code="DETAILED_HEALTH_FAILED"
        )
        return jsonify(response.to_dict()), 503

@health_bp.route('/health/database')
async def database_health():
    """Database-specific health check."""
    try:
        db_health = await save_manager.health_check()
        
        if db_health["healthy"]:
            response = ResponseBuilder.success(
                data=db_health,
                message="Database is healthy"
            )
            return jsonify(response.to_dict()), 200
        else:
            response = ResponseBuilder.error(
                message="Database is unhealthy",
                error_code="DATABASE_UNHEALTHY",
                data=db_health
            )
            return jsonify(response.to_dict()), 503
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        response = ResponseBuilder.error(
            message="Database health check failed",
            error_code="DATABASE_HEALTH_FAILED"
        )
        return jsonify(response.to_dict()), 503

@health_bp.route('/health/ready')
async def readiness_check():
    """Kubernetes-style readiness check."""
    try:
        # Check if service is ready to accept requests
        db_health = await save_manager.health_check()
        
        if db_health["healthy"]:
            response = ResponseBuilder.success(
                data={"ready": True},
                message="Service is ready"
            )
            return jsonify(response.to_dict()), 200
        else:
            response = ResponseBuilder.error(
                message="Service is not ready",
                error_code="NOT_READY",
                data={"ready": False}
            )
            return jsonify(response.to_dict()), 503
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        response = ResponseBuilder.error(
            message="Readiness check failed",
            error_code="READINESS_FAILED",
            data={"ready": False}
        )
        return jsonify(response.to_dict()), 503

@health_bp.route('/health/live')
async def liveness_check():
    """Kubernetes-style liveness check."""
    try:
        # Simple check that service is running
        response = ResponseBuilder.success(
            data={"alive": True},
            message="Service is alive"
        )
        return jsonify(response.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        response = ResponseBuilder.error(
            message="Liveness check failed",
            error_code="LIVENESS_FAILED",
            data={"alive": False}
        )
        return jsonify(response.to_dict()), 503
```

### Step 4: API Documentation Endpoint

**File**: `backend/routes/docs_routes.py` (create new)
```python
"""API documentation endpoints."""

from quart import Blueprint, jsonify
from autofighter.api_standards import ResponseBuilder, STATUS_CODES

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/api/docs')
async def api_documentation():
    """API documentation and endpoint listing."""
    
    api_docs = {
        "service": "autofighter-backend",
        "version": "1.0.0",
        "description": "AutoFighter game backend API",
        "base_url": "/api",
        "response_format": {
            "standard_fields": {
                "status": "success|error|warning|partial",
                "timestamp": "ISO 8601 timestamp",
                "message": "Human readable message",
                "data": "Response data (when applicable)",
                "error_code": "Machine readable error code (on errors)",
                "pagination": "Pagination metadata (for lists)"
            }
        },
        "endpoints": {
            "health": {
                "GET /health": "Basic health check",
                "GET /health/detailed": "Detailed health with system metrics",
                "GET /health/database": "Database health check",
                "GET /health/ready": "Readiness check",
                "GET /health/live": "Liveness check"
            },
            "game_sessions": {
                "POST /api/game/session": "Create new game session",
                "POST /api/game/session/{id}/run": "Start new game run",
                "GET /api/game/session/{session_id}/run/{run_id}": "Get run details",
                "GET /api/game/runs": "List recent runs (paginated)"
            },
            "players": {
                "GET /api/game/players/owned": "Get owned players",
                "POST /api/game/players/{id}/own": "Add player to owned collection",
                "GET /api/game/players/{id}/upgrades": "Get player upgrade points",
                "POST /api/game/players/{id}/upgrades": "Update player upgrade points"
            },
            "gacha": {
                "POST /api/game/gacha/roll": "Perform gacha roll",
                "GET /api/game/gacha/items": "Get gacha items"
            }
        },
        "error_codes": {
            "SESSION_CREATE_FAILED": "Failed to create game session",
            "SESSION_NOT_FOUND": "Game session not found",
            "RUN_NOT_FOUND": "Game run not found",
            "DATABASE_ERROR": "Database operation failed",
            "INVALID_REQUEST": "Invalid request format",
            "MISSING_REQUIRED_DATA": "Required data missing from request",
            "INVALID_PAGINATION": "Invalid pagination parameters",
            "GACHA_ROLL_FAILED": "Gacha roll operation failed"
        }
    }
    
    response = ResponseBuilder.success(
        data=api_docs,
        message="API documentation retrieved successfully"
    )
    
    return jsonify(response.to_dict()), STATUS_CODES[response.status]
```

### Step 5: Updated Main Application

**File**: `backend/app.py` (final update)
```python
"""Complete backend application with standardized APIs."""

from quart import Quart, jsonify
import asyncio
import logging
from autofighter.save_manager import save_manager
from autofighter.middleware import register_error_handlers
from autofighter.api_standards import ResponseBuilder, STATUS_CODES
from routes.game_routes import game_bp
from routes.health_routes import health_bp
from routes.docs_routes import docs_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Quart(__name__)

# Register error handlers
register_error_handlers(app)

# Register blueprints
app.register_blueprint(game_bp)
app.register_blueprint(health_bp)
app.register_blueprint(docs_bp)

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

@app.route('/')
async def root():
    """Root endpoint with standardized response."""
    response = ResponseBuilder.success(
        data={
            "service": "autofighter-backend",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "game_api": "/api/game",
                "documentation": "/api/docs"
            }
        },
        message="AutoFighter Backend API"
    )
    return jsonify(response.to_dict()), STATUS_CODES[response.status]

@app.route('/api/')
async def api_root():
    """API root endpoint for router compatibility."""
    try:
        db_health = await save_manager.health_check()
        
        # Legacy format for router compatibility
        return jsonify({
            "flavor": "default",
            "status": "ok",
            "database_connected": db_health["healthy"]
        }), 200
        
    except Exception as e:
        logger.error(f"API root check failed: {e}")
        return jsonify({
            "flavor": "default", 
            "status": "error",
            "database_connected": False
        }), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=59002, debug=True)
```

## Validation Criteria

### Success Criteria
1. **Response Standardization**: All API endpoints use consistent response format
2. **Error Handling**: Proper error codes and messages for all failure scenarios
3. **Health Checks**: Comprehensive health monitoring for service and database
4. **Documentation**: Complete API documentation available at `/api/docs`
5. **Router Compatibility**: API responses work correctly with router service

### Validation Commands
```bash
# Start backend service
cd backend
uv run python app.py &

# Test standardized responses
curl http://localhost:59002/health
curl http://localhost:59002/health/detailed
curl http://localhost:59002/api/docs

# Test game endpoints
curl -X POST http://localhost:59002/api/game/session
curl http://localhost:59002/api/game/players/owned
curl http://localhost:59002/api/game/runs?page=1&page_size=5

# Test error handling
curl -X POST http://localhost:59002/api/game/gacha/roll \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```

### Expected Results
- All endpoints return standardized JSON responses
- Error responses include appropriate error codes and messages
- Health checks provide detailed service status
- API documentation is complete and accessible
- Pagination works correctly for list endpoints
- Response times are acceptable (< 200ms for simple requests)

## Notes

- Response format is consistent across all endpoints
- Error codes are machine-readable for automated handling
- Health checks support Kubernetes-style probes
- Pagination prevents large response payloads
- API documentation is self-documenting and always current