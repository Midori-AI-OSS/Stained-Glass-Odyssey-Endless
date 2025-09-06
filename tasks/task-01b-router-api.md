# Task 1B: Router API Implementation

## Overview

This task implements the core API routing logic for the router service, including request forwarding to the backend and response standardization.

## Goals

- Implement API request routing and forwarding
- Add standardized error handling
- Create middleware for request/response processing
- Add API endpoint documentation

## Prerequisites

- Task 1A (Router Setup) must be completed
- Router service basic structure in place

## Implementation

### Step 1: API Router Module

**File**: `router/api.py`
```python
"""API routing and forwarding logic."""
import asyncio
import httpx
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from typing import Any, Dict
import logging
from .config import config

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api", tags=["api"])

class RouterException(Exception):
    """Custom exception for router-specific errors."""
    
    def __init__(self, status_code: int, detail: str, backend_error: bool = False):
        self.status_code = status_code
        self.detail = detail
        self.backend_error = backend_error
        super().__init__(detail)

@api_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def forward_request(request: Request, path: str) -> Response:
    """
    Forward requests to backend service with standardized error handling.
    
    Args:
        request: FastAPI request object
        path: API path to forward
        
    Returns:
        Response: Standardized response from backend
        
    Raises:
        HTTPException: On backend communication errors
    """
    backend_url = f"http://{config.backend_host}:{config.backend_port}"
    target_url = f"{backend_url}/api/{path}"
    
    try:
        # Prepare request data
        headers = dict(request.headers)
        headers.pop('host', None)  # Remove host header to avoid conflicts
        
        # Get request body if present
        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
        
        async with httpx.AsyncClient(timeout=config.backend_timeout) as client:
            # Forward request to backend
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            # Return response with proper status code and headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type", "application/json")
            )
            
    except httpx.TimeoutException:
        logger.error(f"Backend timeout for {request.method} {target_url}")
        raise HTTPException(
            status_code=504,
            detail={
                "error": "Gateway Timeout",
                "message": "Backend service did not respond in time",
                "path": path,
                "method": request.method
            }
        )
    except httpx.ConnectError:
        logger.error(f"Backend connection error for {request.method} {target_url}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service Unavailable", 
                "message": "Cannot connect to backend service",
                "path": path,
                "method": request.method
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error forwarding request: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "path": path,
                "method": request.method
            }
        )

@api_router.get("/routes")
async def list_routes() -> Dict[str, Any]:
    """
    List available API routes and their status.
    
    Returns:
        Dict: Available routes and backend connectivity status
    """
    backend_healthy = await check_backend_connectivity()
    
    return {
        "router_version": "0.1.0",
        "backend_status": "healthy" if backend_healthy else "unreachable",
        "available_routes": [
            "/api/game/*",
            "/api/character/*", 
            "/api/battle/*",
            "/api/settings/*"
        ],
        "health_checks": [
            "/health/",
            "/health/backend"
        ]
    }

async def check_backend_connectivity() -> bool:
    """
    Check if backend service is reachable.
    
    Returns:
        bool: True if backend is reachable, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            backend_url = f"http://{config.backend_host}:{config.backend_port}"
            response = await client.get(f"{backend_url}/")
            return response.status_code == 200
    except (httpx.TimeoutException, httpx.ConnectError):
        return False
```

### Step 2: Error Handling Middleware

**File**: `router/middleware.py`
```python
"""Custom middleware for request/response processing."""
import time
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests and responses with timing information."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} {request.url} "
                f"({process_time:.3f}s)"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Error processing {request.method} {request.url}: {e} ({process_time:.3f}s)")
            raise

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Standardize error responses across the API."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "path": str(request.url.path),
                    "method": request.method
                }
            )
```

### Step 3: Update Main Application

**File**: `router/app.py` (updated sections)
```python
"""Main FastAPI router application."""
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import config
from .health import router as health_router
from .api import api_router
from .middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI application
app = FastAPI(
    title="Midori AutoFighter Router",
    description="API Gateway for Midori AutoFighter services",
    version="0.1.0",
    debug=config.debug,
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None
)

# Add middleware (order matters - first added is executed last)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:59001", "http://frontend:59001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(api_router)

@app.get("/")
async def root():
    """
    Router service root endpoint.
    
    Returns:
        dict: Basic service information
    """
    return {
        "service": "midori-autofighter-router",
        "version": "0.1.0",
        "status": "running",
        "environment": config.environment,
        "docs_url": "/docs" if config.debug else "disabled"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.host,
        port=config.port,
        log_level=config.log_level,
        reload=config.debug
    )
```

### Step 4: Testing Module

**File**: `router/test_api.py`
```python
"""Tests for API routing functionality."""
import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from .app import app

client = TestClient(app)

def test_root_endpoint():
    """Test router root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "midori-autofighter-router"
    assert data["status"] == "running"

def test_api_routes_endpoint():
    """Test API routes listing endpoint."""
    response = client.get("/api/routes")
    assert response.status_code == 200
    data = response.json()
    assert "available_routes" in data
    assert "backend_status" in data

@patch('httpx.AsyncClient.request')
async def test_api_forwarding_success(mock_request):
    """Test successful API request forwarding."""
    # Mock successful backend response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"result": "success"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_request.return_value = mock_response
    
    response = client.get("/api/game/status")
    assert response.status_code == 200

@patch('httpx.AsyncClient.request')
async def test_api_forwarding_timeout(mock_request):
    """Test API request timeout handling."""
    # Mock timeout exception
    mock_request.side_effect = httpx.TimeoutException("Request timeout")
    
    response = client.get("/api/game/status")
    assert response.status_code == 504
    data = response.json()
    assert data["detail"]["error"] == "Gateway Timeout"

@patch('httpx.AsyncClient.request')
async def test_api_forwarding_connection_error(mock_request):
    """Test API connection error handling."""
    # Mock connection error
    mock_request.side_effect = httpx.ConnectError("Connection failed")
    
    response = client.get("/api/game/status")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["error"] == "Service Unavailable"

def test_cors_headers():
    """Test CORS headers are properly set."""
    response = client.options("/api/test", headers={"Origin": "http://localhost:59001"})
    assert "access-control-allow-origin" in response.headers

if __name__ == "__main__":
    pytest.main([__file__])
```

## Validation

### Step 1: Import and Syntax Check

```bash
cd router

# Check imports work
uv run python -c "from api import api_router; from middleware import RequestLoggingMiddleware; print('Imports successful')"

# Check app starts with new modules
uv run python -c "from app import app; print('App creation successful')"
```

### Step 2: API Testing

```bash
# Start router service
uv run uvicorn app:app --host 0.0.0.0 --port 59000

# Test in another terminal
curl http://localhost:59000/api/routes
curl -X POST http://localhost:59000/api/test -d '{"test": "data"}' -H "Content-Type: application/json"

# Should return proper error responses since backend is not running
```

### Step 3: Run Tests

```bash
# Run the test suite
uv run pytest test_api.py -v

# Expected: All tests should pass
```

## Completion Criteria

- [ ] API routing module implemented with request forwarding
- [ ] Error handling middleware working properly
- [ ] Logging middleware capturing requests/responses
- [ ] Updated main application includes new modules
- [ ] Test suite passes all API routing tests
- [ ] Documentation updated with API information

## Next Steps

After completing this task, proceed to **Task 1C: Router Integration** to add service discovery and advanced health monitoring.