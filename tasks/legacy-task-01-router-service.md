# Task 01: Router Service Implementation

## Objective
Create a lightweight FastAPI-based router service that acts as an API gateway between the frontend and backend services. This service will be the single entry point for all client requests.

## Requirements

### 1. Service Setup
- **Technology**: FastAPI (lightweight, async, automatic OpenAPI docs)
- **Port**: 59000 (new dedicated port)
- **Location**: `router/` directory in project root
- **Dependencies**: FastAPI, uvicorn, httpx, pydantic

### 2. Core Functionality

#### 2.1 Request Routing
- Route all `/api/*` requests to backend service (http://backend:59002)
- Route static asset requests to appropriate services
- Maintain request/response headers and HTTP methods
- Support WebSocket connections if needed

#### 2.2 Service Discovery
- Health check endpoints for all services
- Automatic backend discovery with fallback
- Configuration via environment variables
- Graceful handling of service unavailability

#### 2.3 Response Standardization
- Consistent error response format
- Request/response logging
- CORS handling (centralized)
- Request timeout management

### 3. File Structure
```
router/
├── app.py                 # Main FastAPI application
├── config.py             # Configuration management
├── routes/
│   ├── __init__.py
│   ├── health.py         # Health check endpoints
│   ├── proxy.py          # Backend proxy routes
│   └── static.py         # Static asset routes
├── middleware/
│   ├── __init__.py
│   ├── cors.py           # CORS middleware
│   ├── logging.py        # Request logging
│   └── error_handling.py # Error standardization
├── utils/
│   ├── __init__.py
│   ├── service_discovery.py # Backend discovery
│   └── http_client.py    # HTTP client configuration
├── requirements.txt      # Dependencies
├── Dockerfile           # Container configuration
└── .env.example         # Environment configuration template
```

## Implementation Tasks

### Task 1.1: Project Setup
**File**: `router/pyproject.toml`
```toml
[project]
name = "midori-autofighter-router"
version = "0.1.0"
description = "API Router service for Midori AutoFighter"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "httpx>=0.25.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
]
```

**Setup Commands**:
```bash
# Create router directory
mkdir -p router
cd router

# Initialize uv project
uv init --no-readme
# Add dependencies
uv add fastapi uvicorn[standard] httpx pydantic python-dotenv
# Add dev dependencies  
uv add --dev pytest pytest-asyncio
```

**File**: `router/.env.example`
```env
# Router Configuration
ROUTER_HOST=0.0.0.0
ROUTER_PORT=59000
LOG_LEVEL=INFO

# Backend Service
BACKEND_HOST=backend
BACKEND_PORT=59002
BACKEND_TIMEOUT=30

# Frontend Service  
FRONTEND_HOST=frontend
FRONTEND_PORT=59001

# Database Service
DATABASE_HOST=database
DATABASE_PORT=5432
```

### Task 1.2: Core Application
**File**: `router/app.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routes import health, proxy, static
from middleware.logging import LoggingMiddleware
from middleware.error_handling import ErrorHandlingMiddleware

load_dotenv()

app = FastAPI(
    title="Midori AutoFighter Router",
    description="API Gateway for AutoFighter services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(proxy.router, prefix="/api", tags=["proxy"])
app.include_router(static.router, tags=["static"])

@app.get("/")
async def root():
    return {
        "service": "midori-autofighter-router",
        "status": "ok",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("ROUTER_HOST", "0.0.0.0"),
        port=int(os.getenv("ROUTER_PORT", 59000)),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=True
    )
```

### Task 1.3: Configuration Management
**File**: `router/config.py`
```python
from pydantic_settings import BaseSettings
from typing import Optional

class RouterSettings(BaseSettings):
    # Router settings
    router_host: str = "0.0.0.0"
    router_port: int = 59000
    log_level: str = "INFO"
    
    # Backend service
    backend_host: str = "backend"
    backend_port: int = 59002
    backend_timeout: int = 30
    
    # Frontend service
    frontend_host: str = "frontend"
    frontend_port: int = 59001
    
    # Database service
    database_host: str = "database"
    database_port: int = 5432
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = RouterSettings()
```

### Task 1.4: Health Check Routes
**File**: `router/routes/health.py`
```python
from fastapi import APIRouter, HTTPException
import httpx
import asyncio
from datetime import datetime
from config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """Overall system health check"""
    services = await check_all_services()
    
    overall_status = "healthy" if all(
        service["status"] == "healthy" 
        for service in services.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }

@router.get("/backend")
async def backend_health():
    """Backend service health check"""
    return await check_service_health(
        f"http://{settings.backend_host}:{settings.backend_port}",
        "backend"
    )

@router.get("/frontend")  
async def frontend_health():
    """Frontend service health check"""
    return await check_service_health(
        f"http://{settings.frontend_host}:{settings.frontend_port}",
        "frontend"
    )

async def check_all_services():
    """Check health of all services concurrently"""
    tasks = [
        check_service_health(
            f"http://{settings.backend_host}:{settings.backend_port}",
            "backend"
        ),
        check_service_health(
            f"http://{settings.frontend_host}:{settings.frontend_port}",
            "frontend"
        )
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "backend": results[0] if not isinstance(results[0], Exception) 
                  else {"status": "unhealthy", "error": str(results[0])},
        "frontend": results[1] if not isinstance(results[1], Exception) 
                   else {"status": "unhealthy", "error": str(results[1])}
    }

async def check_service_health(url: str, service_name: str):
    """Check health of a specific service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/")
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "url": url
                }
            else:
                return {
                    "status": "unhealthy",
                    "status_code": response.status_code,
                    "url": url
                }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "url": url
        }
```

### Task 1.5: Proxy Routes
**File**: `router/routes/proxy.py`
```python
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import httpx
import json
from config import settings

router = APIRouter()

# Create HTTP client for backend communication
backend_client = httpx.AsyncClient(
    base_url=f"http://{settings.backend_host}:{settings.backend_port}",
    timeout=settings.backend_timeout
)

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_to_backend(request: Request, path: str):
    """Proxy all API requests to backend service"""
    
    try:
        # Prepare request data
        url = f"/{path}"
        if request.query_params:
            url += f"?{request.query_params}"
        
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Forward request to backend
        response = await backend_client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=body
        )
        
        # Return response with same status code and headers
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Backend service unavailable",
                "service": "backend",
                "action": "retry_later"
            }
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "Backend service timeout",
                "service": "backend", 
                "timeout": settings.backend_timeout
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Proxy error",
                "message": str(e)
            }
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up HTTP client on shutdown"""
    await backend_client.aclose()
```

### Task 1.6: Error Handling Middleware
**File**: `router/middleware/error_handling.py`
```python
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            logger.exception(f"Unhandled error in router: {e}")
            
            error_response = {
                "error": "Internal server error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path,
                "method": request.method
            }
            
            # Include traceback in development
            if logger.level == logging.DEBUG:
                error_response["traceback"] = traceback.format_exc()
            
            response = JSONResponse(
                content=error_response,
                status_code=500
            )
            
            await response(scope, receive, send)
```

### Task 1.7: Docker Configuration
**File**: `router/Dockerfile`
```dockerfile
FROM lunamidori5/pixelarch:quartz

EXPOSE 59000

ENV PYTHONOPTIMIZE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

# Update OS release info for clarity
RUN sudo sed -i 's/Quartz/Router-uv-server/g' /etc/os-release

# Install uv (may already be installed in base image)
RUN yay -Syu --noconfirm uv && yay -Yccc --noconfirm

# Ensure uv is on PATH
ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="/app"

# UV cache directory
ENV UV_CACHE_DIR="/.cache"

WORKDIR /app

# Setup directories and permissions
RUN sudo chown -R $(whoami):$(whoami) /app
RUN sudo mkdir -p ${UV_CACHE_DIR} && sudo chown -R $(whoami):$(whoami) ${UV_CACHE_DIR} && sudo chmod -R 755 ${UV_CACHE_DIR}
RUN sudo mkdir -p /.venv && sudo chown -R $(whoami):$(whoami) /.venv && sudo chmod -R 755 /.venv

# Do not copy source; it will be bind-mounted at runtime

# Run application using uv
CMD ["bash", "-lc", "cd /app && uv run uvicorn app:app --host 0.0.0.0 --port 59000"]
```

**File**: `router/docker-entrypoint.sh`
```bash
#!/bin/bash
set -e

echo "Installing dependencies with uv..."
uv sync --frozen

echo "Starting router service..."
exec uv run uvicorn app:app --host 0.0.0.0 --port 59000
```

## Validation

### Task 1.8: Create Validation Script
**File**: `router/validate.py`
```python
#!/usr/bin/env python3
"""Validation script for router service"""

import asyncio
import httpx
import sys

async def validate_router():
    """Validate router service functionality"""
    
    print("🔍 Validating Router Service...")
    
    base_url = "http://localhost:59000"
    
    try:
        async with httpx.AsyncClient() as client:
            # Test root endpoint
            print("  ✓ Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "midori-autofighter-router"
            
            # Test health endpoint
            print("  ✓ Testing health endpoint...")
            response = await client.get(f"{base_url}/health/")
            assert response.status_code in [200, 503]  # May be degraded if backend down
            
            # Test API docs
            print("  ✓ Testing API documentation...")
            response = await client.get(f"{base_url}/docs")
            assert response.status_code == 200
            
            print("✅ Router service validation passed!")
            return True
            
    except Exception as e:
        print(f"❌ Router service validation failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(validate_router())
    sys.exit(0 if result else 1)
```

## Testing Commands

```bash
# Run router service locally
cd router
pip install -r requirements.txt
python app.py

# Validate service
python validate.py

# Test endpoints
curl http://localhost:59000/
curl http://localhost:59000/health/
curl http://localhost:59000/docs
```

## Completion Criteria

- [ ] All files created according to specification
- [ ] Router service starts without errors on port 59000
- [ ] Health endpoints respond correctly
- [ ] API documentation accessible at `/docs`
- [ ] Validation script passes all tests
- [ ] Docker container builds and runs successfully

## Notes for Task Master Review

- Router service provides single entry point for frontend
- Health checks enable service monitoring and debugging
- Error handling provides consistent error responses
- Configuration enables environment-based deployment
- Middleware architecture supports extensibility

**Next Task**: After completion and review, proceed to `task-02-database-migration.md`