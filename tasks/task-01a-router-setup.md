# Task 1A: Router Service Setup

## Overview

This task creates the basic foundation for the FastAPI router service that will act as the central API gateway for all frontend-backend communication.

## Goals

- Create router service project structure
- Setup basic FastAPI application with uv
- Implement basic health check endpoint
- Create Docker configuration using pixelarch base

## Project Structure

```
router/
├── pyproject.toml        # uv project configuration
├── app.py                # Main FastAPI application
├── config.py            # Configuration management
├── health.py            # Health check endpoints
├── Dockerfile           # Docker configuration  
├── docker-entrypoint.sh # Docker startup script
├── .env.example         # Environment template
└── README.md            # Service documentation
```

## Implementation

### Step 1: Project Setup

**Create Directory and Initialize uv Project**:
```bash
# Create router directory
mkdir -p router
cd router

# Initialize uv project
uv init --no-readme

# Add core dependencies
uv add fastapi uvicorn[standard] httpx pydantic python-dotenv

# Add development dependencies  
uv add --dev pytest pytest-asyncio
```

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

### Step 2: Basic Configuration

**File**: `router/.env.example`
```env
# Router Configuration
ROUTER_HOST=0.0.0.0
ROUTER_PORT=59000
LOG_LEVEL=info

# Backend Service
BACKEND_HOST=backend
BACKEND_PORT=59002
BACKEND_TIMEOUT=30

# Development settings
ENVIRONMENT=development
DEBUG=false
```

**File**: `router/config.py`
```python
"""Router service configuration."""
from pydantic import BaseSettings
from typing import Literal

class RouterConfig(BaseSettings):
    """Router service configuration settings."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 59000
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    
    # Backend service settings
    backend_host: str = "backend"
    backend_port: int = 59002
    backend_timeout: int = 30
    
    # Environment settings
    environment: Literal["development", "production"] = "development"
    debug: bool = False
    
    class Config:
        env_prefix = "ROUTER_"
        env_file = ".env"

# Global config instance
config = RouterConfig()
```

### Step 3: Health Check Implementation

**File**: `router/health.py`
```python
"""Health check endpoints for router service."""
import asyncio
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from .config import config

router = APIRouter(prefix="/health", tags=["health"])

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    backend_status: str

@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Router service health check.
    
    Returns:
        HealthResponse: Service health status including backend connectivity
    """
    # Check backend connectivity
    backend_status = await check_backend_health()
    
    return HealthResponse(
        status="healthy",
        service="router",
        version="0.1.0",
        backend_status=backend_status
    )

@router.get("/backend")
async def backend_health() -> Dict[str, Any]:
    """
    Check backend service health specifically.
    
    Returns:
        Dict: Backend health status and details
        
    Raises:
        HTTPException: If backend is not reachable
    """
    try:
        async with httpx.AsyncClient(timeout=config.backend_timeout) as client:
            backend_url = f"http://{config.backend_host}:{config.backend_port}"
            response = await client.get(f"{backend_url}/")
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "backend_url": backend_url,
                    "response_time": response.elapsed.total_seconds(),
                    "backend_data": response.json()
                }
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Backend returned status {response.status_code}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Backend timeout - service may be down"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to backend service"
        )

async def check_backend_health() -> str:
    """
    Internal backend health check helper.
    
    Returns:
        str: Backend health status ("healthy", "unhealthy", "timeout")
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            backend_url = f"http://{config.backend_host}:{config.backend_port}"
            response = await client.get(f"{backend_url}/")
            return "healthy" if response.status_code == 200 else "unhealthy"
    except (httpx.TimeoutException, httpx.ConnectError):
        return "unreachable"
```

### Step 4: Main Application

**File**: `router/app.py`
```python
"""Main FastAPI router application."""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import config
from .health import router as health_router

# Create FastAPI application
app = FastAPI(
    title="Midori AutoFighter Router",
    description="API Gateway for Midori AutoFighter services",
    version="0.1.0",
    debug=config.debug
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:59001", "http://frontend:59001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health check routes
app.include_router(health_router)

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
        "environment": config.environment
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

### Step 5: Docker Configuration

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

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Do not copy source; it will be bind-mounted at runtime

# Run application using entrypoint
CMD ["bash", "/app/docker-entrypoint.sh"]
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

### Step 6: Documentation

**File**: `router/README.md`
```markdown
# Midori AutoFighter Router Service

FastAPI-based API gateway that coordinates communication between frontend and backend services.

## Features

- Health check endpoints for service monitoring
- CORS configuration for frontend communication  
- Backend service connectivity validation
- Environment-based configuration
- uv-based dependency management

## Development

```bash
# Install dependencies
uv sync

# Run development server
uv run python app.py

# Run with uvicorn directly
uv run uvicorn app:app --host 0.0.0.0 --port 59000 --reload
```

## Docker

```bash
# Build image
docker build -t midori-router .

# Run container (with mounted source)
docker run -v $(pwd):/app -p 59000:59000 midori-router
```

## Environment Variables

See `.env.example` for configuration options.

## Health Checks

- `GET /` - Basic service info
- `GET /health/` - Service and backend health
- `GET /health/backend` - Detailed backend connectivity
```

## Validation

### Step 1: Local Testing

```bash
cd router

# Install dependencies
uv sync

# Test basic startup
uv run python -c "from app import app; print('Import successful')"

# Run development server
uv run uvicorn app:app --host 0.0.0.0 --port 59000
```

### Step 2: Health Check Testing

```bash
# Test health endpoint (in another terminal)
curl http://localhost:59000/
curl http://localhost:59000/health/

# Expected responses
# Root: {"service": "midori-autofighter-router", "version": "0.1.0", ...}
# Health: {"status": "healthy", "service": "router", ...}
```

### Step 3: Docker Testing

```bash
# Build Docker image
docker build -t midori-router .

# Test with mounted volume
docker run --rm -v $(pwd):/app -p 59000:59000 midori-router
```

## Completion Criteria

- [ ] Router directory created with uv project structure
- [ ] FastAPI application starts successfully on port 59000
- [ ] Health check endpoints return proper responses
- [ ] Docker image builds and runs successfully
- [ ] Basic configuration system working
- [ ] All validation tests pass

## Next Steps

After completing this task, proceed to **Task 1B: Router API Implementation** to add the actual routing logic and API endpoints.