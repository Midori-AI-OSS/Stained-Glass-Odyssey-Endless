# Task 1C: Router Integration

## Overview

This task completes the router service implementation by adding service discovery, health checks, and integration testing to ensure the router can properly communicate with backend services.

## Goals

- Implement service discovery and health check mechanisms
- Add comprehensive logging and monitoring
- Create integration tests for router functionality
- Validate router-backend communication

## Prerequisites

- Task 1A (Router Setup) must be completed
- Task 1B (Router API) must be completed
- Backend service running on port 59002

## Implementation

### Step 1: Service Discovery Module

**File**: `router/discovery.py`
```python
"""Service discovery and health check utilities."""
import asyncio
import httpx
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from .config import config

logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    """Service health status information."""
    name: str
    url: str
    healthy: bool
    last_check: datetime
    response_time: Optional[float] = None
    error: Optional[str] = None

class ServiceDiscovery:
    """Manages service discovery and health checks."""
    
    def __init__(self):
        self.services: Dict[str, ServiceStatus] = {}
        self.client = httpx.AsyncClient(timeout=5.0)
        
    async def register_service(self, name: str, url: str) -> None:
        """Register a service for health monitoring."""
        self.services[name] = ServiceStatus(
            name=name,
            url=url,
            healthy=False,
            last_check=datetime.now()
        )
        logger.info(f"Registered service: {name} at {url}")
        
    async def check_service_health(self, name: str) -> ServiceStatus:
        """Check health of a specific service."""
        if name not in self.services:
            raise ValueError(f"Service {name} not registered")
            
        service = self.services[name]
        start_time = datetime.now()
        
        try:
            response = await self.client.get(f"{service.url}/health")
            response_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                service.healthy = True
                service.response_time = response_time
                service.error = None
                logger.debug(f"Service {name} is healthy (response: {response_time:.3f}s)")
            else:
                service.healthy = False
                service.error = f"HTTP {response.status_code}"
                logger.warning(f"Service {name} unhealthy: {service.error}")
                
        except Exception as e:
            service.healthy = False
            service.error = str(e)
            service.response_time = None
            logger.error(f"Service {name} health check failed: {e}")
            
        service.last_check = datetime.now()
        return service
        
    async def check_all_services(self) -> Dict[str, ServiceStatus]:
        """Check health of all registered services."""
        tasks = [
            self.check_service_health(name) 
            for name in self.services.keys()
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
        return self.services.copy()
        
    async def get_healthy_service_url(self, service_name: str) -> Optional[str]:
        """Get URL of a healthy service instance."""
        if service_name in self.services:
            await self.check_service_health(service_name)
            service = self.services[service_name]
            if service.healthy:
                return service.url
                
        return None
        
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()

# Global service discovery instance
discovery = ServiceDiscovery()
```

### Step 2: Enhanced Health Check Routes

**File**: `router/health.py` (update existing)
```python
"""Enhanced health check endpoints with service monitoring."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from datetime import datetime
from .discovery import discovery

logger = logging.getLogger(__name__)
health_router = APIRouter(tags=["health"])

@health_router.get("/health")
async def router_health() -> Dict[str, Any]:
    """Router service health check."""
    return {
        "status": "healthy",
        "service": "router",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@health_router.get("/health/detailed")
async def detailed_health() -> Dict[str, Any]:
    """Detailed health check including backend services."""
    
    # Check all registered services
    service_statuses = await discovery.check_all_services()
    
    # Overall system health
    all_healthy = all(service.healthy for service in service_statuses.values())
    
    health_data = {
        "status": "healthy" if all_healthy else "degraded",
        "router": {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        },
        "services": {}
    }
    
    # Add service status details
    for name, status in service_statuses.items():
        health_data["services"][name] = {
            "healthy": status.healthy,
            "last_check": status.last_check.isoformat(),
            "response_time": status.response_time,
            "error": status.error
        }
    
    return health_data

@health_router.get("/health/services/{service_name}")
async def service_health(service_name: str) -> Dict[str, Any]:
    """Health check for a specific service."""
    try:
        status = await discovery.check_service_health(service_name)
        return {
            "service": service_name,
            "healthy": status.healthy,
            "last_check": status.last_check.isoformat(),
            "response_time": status.response_time,
            "error": status.error
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Step 3: Update Main Application

**File**: `router/app.py` (update existing)
```python
"""Main FastAPI router application with service discovery."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import config
from .health import health_router
from .api import api_router  # From Task 1B
from .discovery import discovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting router service...")
    
    # Register backend service for monitoring
    backend_url = f"http://{config.backend_host}:{config.backend_port}"
    await discovery.register_service("backend", backend_url)
    
    # Initial health check
    logger.info("Performing initial service health checks...")
    await discovery.check_all_services()
    
    yield
    
    # Shutdown
    logger.info("Shutting down router service...")
    await discovery.close()

# Create FastAPI application
app = FastAPI(
    title="AutoFighter Router Service",
    description="API gateway for AutoFighter game services",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "autofighter-router",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=config.port,
        reload=config.debug
    )
```

### Step 4: Integration Tests

**File**: `router/tests/test_integration.py`
```python
"""Integration tests for router service."""
import pytest
import httpx
import asyncio
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_service_discovery():
    """Test service discovery functionality."""
    from router.discovery import ServiceDiscovery
    
    discovery = ServiceDiscovery()
    
    # Register a mock service
    await discovery.register_service("test", "http://localhost:8000")
    
    # Mock successful health check
    with patch.object(discovery.client, 'get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        status = await discovery.check_service_health("test")
        assert status.healthy is True
        assert status.error is None
    
    await discovery.close()

@pytest.mark.asyncio 
async def test_health_endpoints():
    """Test health check endpoints."""
    from router.app import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Basic health check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Detailed health check
    response = client.get("/health/detailed")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "services" in response.json()

@pytest.mark.asyncio
async def test_api_forwarding():
    """Test API request forwarding to backend."""
    from router.app import app
    from fastapi.testclient import TestClient
    
    with patch('router.api.httpx.AsyncClient') as mock_client:
        # Mock backend response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.headers = {"content-type": "application/json"}
        
        mock_client.return_value.request.return_value = mock_response
        
        client = TestClient(app)
        response = client.get("/api/test")
        
        # Should forward request successfully
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_backend_unavailable():
    """Test router behavior when backend is unavailable."""
    from router.discovery import ServiceDiscovery
    
    discovery = ServiceDiscovery()
    await discovery.register_service("backend", "http://invalid:59002")
    
    # Health check should fail gracefully
    status = await discovery.check_service_health("backend")
    assert status.healthy is False
    assert status.error is not None
    
    await discovery.close()
```

### Step 5: Validation Script

**File**: `router/validate_integration.py`
```python
#!/usr/bin/env python3
"""Integration validation script for router service."""

import asyncio
import httpx
import sys
from typing import Dict, Any

async def validate_integration():
    """Validate router integration with backend services."""
    
    print("🔍 Validating Router Integration...")
    
    router_url = "http://localhost:59000"
    backend_url = "http://localhost:59002"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Router health
        print("1. Testing router health...")
        try:
            response = await client.get(f"{router_url}/health")
            assert response.status_code == 200
            print("   ✅ Router health check passed")
        except Exception as e:
            print(f"   ❌ Router health check failed: {e}")
            return False
            
        # Test 2: Detailed health with services
        print("2. Testing detailed health check...")
        try:
            response = await client.get(f"{router_url}/health/detailed")
            assert response.status_code == 200
            data = response.json()
            assert "services" in data
            print("   ✅ Detailed health check passed")
        except Exception as e:
            print(f"   ❌ Detailed health check failed: {e}")
            return False
            
        # Test 3: Backend health via router
        print("3. Testing backend health via router...")
        try:
            response = await client.get(f"{router_url}/health/services/backend")
            data = response.json()
            if data["healthy"]:
                print("   ✅ Backend is healthy via router")
            else:
                print(f"   ⚠️  Backend unhealthy: {data['error']}")
        except Exception as e:
            print(f"   ❌ Backend health check failed: {e}")
            
        # Test 4: API forwarding
        print("4. Testing API request forwarding...")
        try:
            response = await client.get(f"{router_url}/api/")
            if response.status_code == 200:
                print("   ✅ API forwarding working")
            else:
                print(f"   ⚠️  API forwarding status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ API forwarding failed: {e}")
    
    print("\n🎉 Router integration validation complete!")
    return True

if __name__ == "__main__":
    success = asyncio.run(validate_integration())
    sys.exit(0 if success else 1)
```

## Validation Criteria

### Success Criteria
1. **Service Discovery**: Router can discover and monitor backend service
2. **Health Checks**: All health endpoints return appropriate responses
3. **API Forwarding**: Requests are properly forwarded to backend
4. **Error Handling**: Router handles backend unavailability gracefully
5. **Integration Tests**: All tests pass successfully

### Validation Commands
```bash
# Run integration tests
cd router
uv run pytest tests/test_integration.py -v

# Run integration validation
uv run python validate_integration.py

# Test service discovery manually
curl http://localhost:59000/health/detailed
curl http://localhost:59000/health/services/backend
```

### Expected Results
- Router starts successfully and registers backend service
- Health checks show service status accurately
- API requests are forwarded correctly
- Service discovery handles failures gracefully
- All integration tests pass

## Notes

- Ensure backend is running on port 59002 before testing
- Router service discovery will show backend as unhealthy if it's not running
- Integration tests can run with mocked backend for development
- Service discovery enables future load balancing and failover capabilities