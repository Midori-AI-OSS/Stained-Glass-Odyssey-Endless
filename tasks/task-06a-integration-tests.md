# Task 6A: Integration Tests

## Overview

This task implements comprehensive integration tests for service communication, API functionality, and end-to-end workflows to ensure the complete architecture works correctly.

## Goals

- Create integration tests for service-to-service communication
- Test API endpoints and data flow through the system
- Validate database operations and data persistence
- Implement automated testing for the complete workflow
- Add performance and load testing capabilities

## Prerequisites

- All services (router, backend, frontend, database) implemented and running
- Docker Compose environment set up
- Testing frameworks available (pytest, jest, etc.)

## Implementation

### Step 1: Backend Integration Tests

**File**: `tests/integration/test_backend_integration.py`
```python
"""
Integration tests for backend service
"""

import pytest
import asyncio
import httpx
import psycopg2
import json
from typing import Dict, Any
import uuid
import time

class TestBackendIntegration:
    """Integration tests for backend service with real database."""
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        return "http://localhost:59002"
    
    @pytest.fixture(scope="class")
    def database_config(self):
        return {
            "host": "localhost",
            "port": 5432,
            "database": "autofighter", 
            "user": "autofighter",
            "password": "password"
        }
    
    @pytest.fixture(scope="class")
    async def http_client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture(scope="class")
    def db_connection(self, database_config):
        conn = psycopg2.connect(**database_config)
        yield conn
        conn.close()
    
    async def test_backend_health(self, http_client, backend_url):
        """Test backend health endpoint."""
        response = await http_client.get(f"{backend_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] in ["healthy", "degraded"]
    
    async def test_backend_root(self, http_client, backend_url):
        """Test backend root endpoint."""
        response = await http_client.get(f"{backend_url}/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "autofighter-backend" in data["data"]["service"]
    
    async def test_api_root_compatibility(self, http_client, backend_url):
        """Test API root endpoint for router compatibility."""
        response = await http_client.get(f"{backend_url}/api/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["flavor"] == "default"
        assert data["status"] == "ok"
        assert "database_connected" in data
    
    async def test_game_session_lifecycle(self, http_client, backend_url):
        """Test complete game session lifecycle."""
        # Create session
        response = await http_client.post(f"{backend_url}/api/game/session")
        assert response.status_code == 201
        
        session_data = response.json()
        assert session_data["status"] == "success"
        session_id = session_data["data"]["session_id"]
        assert session_id is not None
        
        # Start run
        party = {"player1": {"name": "Test Player", "level": 1}}
        map_config = {"level": 1, "area": "test"}
        
        response = await http_client.post(
            f"{backend_url}/api/game/session/{session_id}/run",
            json={"party": party, "map": map_config}
        )
        assert response.status_code == 201
        
        run_data = response.json()
        assert run_data["status"] == "success"
        run_id = run_data["data"]["run_id"]
        
        # Get run details
        response = await http_client.get(
            f"{backend_url}/api/game/session/{session_id}/run/{run_id}"
        )
        assert response.status_code == 200
        
        run_details = response.json()
        assert run_details["status"] == "success"
        assert run_details["data"]["party"] == party
        assert run_details["data"]["map"] == map_config
    
    async def test_owned_players_workflow(self, http_client, backend_url):
        """Test owned players management workflow."""
        player_id = f"test_player_{uuid.uuid4().hex[:8]}"
        player_data = {"name": "Integration Test Player", "class": "warrior"}
        
        # Add owned player
        response = await http_client.post(
            f"{backend_url}/api/game/players/{player_id}/own",
            json={"player_data": player_data}
        )
        assert response.status_code == 201
        
        add_response = response.json()
        assert add_response["status"] == "success"
        
        # Get owned players
        response = await http_client.get(f"{backend_url}/api/game/players/owned")
        assert response.status_code == 200
        
        owned_data = response.json()
        assert owned_data["status"] == "success"
        assert player_id in owned_data["data"]["players"]
    
    async def test_gacha_system_workflow(self, http_client, backend_url):
        """Test gacha system workflow."""
        player_id = "test_gacha_player"
        
        # Perform gacha roll
        response = await http_client.post(
            f"{backend_url}/api/game/gacha/roll",
            json={"player_id": player_id, "type": "standard"}
        )
        assert response.status_code == 201
        
        roll_data = response.json()
        assert roll_data["status"] == "success"
        assert "roll_id" in roll_data["data"]
        assert len(roll_data["data"]["items"]) > 0
        
        # Get gacha items
        response = await http_client.get(f"{backend_url}/api/game/gacha/items?limit=10")
        assert response.status_code == 200
        
        items_data = response.json()
        assert items_data["status"] == "success"
        assert len(items_data["data"]["items"]) > 0
    
    async def test_upgrade_points_workflow(self, http_client, backend_url):
        """Test upgrade points workflow."""
        player_id = f"upgrade_test_{uuid.uuid4().hex[:8]}"
        
        # Get initial upgrade points (should be defaults)
        response = await http_client.get(
            f"{backend_url}/api/game/players/{player_id}/upgrades"
        )
        assert response.status_code == 200
        
        initial_data = response.json()
        assert initial_data["status"] == "success"
        assert initial_data["data"]["points"] == 0
        
        # Update upgrade points
        response = await http_client.post(
            f"{backend_url}/api/game/players/{player_id}/upgrades",
            json={
                "points_delta": 100,
                "stat_upgrades": {"hp": 10, "atk": 5}
            }
        )
        assert response.status_code == 200
        
        update_data = response.json()
        assert update_data["status"] == "success"
        assert update_data["data"]["points"] == 100
        assert update_data["data"]["hp"] == 10
        assert update_data["data"]["atk"] == 5
    
    def test_database_connectivity(self, db_connection):
        """Test direct database connectivity and schema."""
        cursor = db_connection.cursor()
        
        # Test basic connectivity
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        # Verify tables exist
        tables = ["runs", "owned_players", "gacha_items", "gacha_rolls", "upgrade_points"]
        for table in tables:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s",
                (table,)
            )
            assert cursor.fetchone()[0] == 1
        
        cursor.close()
    
    def test_database_operations(self, db_connection):
        """Test database operations directly."""
        cursor = db_connection.cursor()
        
        # Insert test data
        test_player_id = f"db_test_{uuid.uuid4().hex[:8]}"
        cursor.execute(
            "INSERT INTO owned_players (legacy_id, player_data) VALUES (%s, %s)",
            (test_player_id, json.dumps({"name": "DB Test Player"}))
        )
        db_connection.commit()
        
        # Verify insertion
        cursor.execute(
            "SELECT player_data FROM owned_players WHERE legacy_id = %s",
            (test_player_id,)
        )
        result = cursor.fetchone()
        assert result is not None
        
        player_data = json.loads(result[0])
        assert player_data["name"] == "DB Test Player"
        
        # Cleanup
        cursor.execute(
            "DELETE FROM owned_players WHERE legacy_id = %s",
            (test_player_id,)
        )
        db_connection.commit()
        cursor.close()

    async def test_error_handling(self, http_client, backend_url):
        """Test API error handling."""
        # Test invalid session
        response = await http_client.get(
            f"{backend_url}/api/game/session/invalid-session/run/invalid-run"
        )
        assert response.status_code == 404
        
        error_data = response.json()
        assert error_data["status"] == "error"
        assert "not found" in error_data["message"].lower()
        
        # Test invalid request data
        response = await http_client.post(
            f"{backend_url}/api/game/gacha/roll",
            json={"invalid": "data"}
        )
        assert response.status_code == 400
        
        error_data = response.json()
        assert error_data["status"] == "error"
    
    async def test_pagination(self, http_client, backend_url):
        """Test API pagination."""
        response = await http_client.get(
            f"{backend_url}/api/game/runs?page=1&page_size=5"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "pagination" in data
        
        pagination = data["pagination"]
        assert pagination["current_page"] == 1
        assert pagination["page_size"] == 5

@pytest.mark.asyncio
class TestPerformance:
    """Performance tests for backend service."""
    
    @pytest.fixture
    def backend_url(self):
        return "http://localhost:59002"
    
    async def test_health_check_performance(self, backend_url):
        """Test health check response time."""
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.get(f"{backend_url}/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            assert response_time < 1.0  # Should respond within 1 second
    
    async def test_concurrent_requests(self, backend_url):
        """Test handling concurrent requests."""
        async with httpx.AsyncClient() as client:
            # Create multiple concurrent health check requests
            tasks = []
            for i in range(10):
                task = client.get(f"{backend_url}/health")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Should handle 10 concurrent requests quickly
            total_time = end_time - start_time
            assert total_time < 5.0
    
    async def test_session_creation_load(self, backend_url):
        """Test session creation under load."""
        async with httpx.AsyncClient() as client:
            # Create multiple sessions concurrently
            tasks = []
            for i in range(5):
                task = client.post(f"{backend_url}/api/game/session")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All session creations should succeed
            for response in responses:
                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "success"
                assert "session_id" in data["data"]
```

### Step 2: Router Integration Tests

**File**: `tests/integration/test_router_integration.py`
```python
"""
Integration tests for router service
"""

import pytest
import asyncio
import httpx
import time

class TestRouterIntegration:
    """Integration tests for router service."""
    
    @pytest.fixture(scope="class")
    def router_url(self):
        return "http://localhost:59000"
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        return "http://localhost:59002"
    
    @pytest.fixture(scope="class")
    async def http_client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    async def test_router_health(self, http_client, router_url):
        """Test router health endpoint."""
        response = await http_client.get(f"{router_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "router" in data["data"]["service"].lower()
    
    async def test_router_detailed_health(self, http_client, router_url):
        """Test router detailed health with backend status."""
        response = await http_client.get(f"{router_url}/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "services" in data["data"]
        assert "backend" in data["data"]["services"]
    
    async def test_api_forwarding(self, http_client, router_url):
        """Test API request forwarding to backend."""
        # Test API root forwarding
        response = await http_client.get(f"{router_url}/api/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["flavor"] == "default"
        assert data["status"] == "ok"
    
    async def test_session_creation_through_router(self, http_client, router_url):
        """Test session creation through router."""
        response = await http_client.post(f"{router_url}/api/game/session")
        assert response.status_code == 201
        
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data["data"]
    
    async def test_complete_workflow_through_router(self, http_client, router_url):
        """Test complete game workflow through router."""
        # Create session
        response = await http_client.post(f"{router_url}/api/game/session")
        assert response.status_code == 201
        session_id = response.json()["data"]["session_id"]
        
        # Start run
        party = {"player1": {"name": "Router Test", "level": 1}}
        map_config = {"level": 1, "area": "router_test"}
        
        response = await http_client.post(
            f"{router_url}/api/game/session/{session_id}/run",
            json={"party": party, "map": map_config}
        )
        assert response.status_code == 201
        run_id = response.json()["data"]["run_id"]
        
        # Get run details
        response = await http_client.get(
            f"{router_url}/api/game/session/{session_id}/run/{run_id}"
        )
        assert response.status_code == 200
        
        run_data = response.json()
        assert run_data["data"]["party"] == party
        assert run_data["data"]["map"] == map_config
    
    async def test_error_forwarding(self, http_client, router_url):
        """Test error forwarding from backend."""
        # Test invalid endpoint
        response = await http_client.get(f"{router_url}/api/invalid-endpoint")
        assert response.status_code == 404
    
    async def test_router_performance(self, http_client, router_url):
        """Test router performance."""
        start_time = time.time()
        response = await http_client.get(f"{router_url}/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Router should be very fast
    
    async def test_concurrent_routing(self, http_client, router_url):
        """Test concurrent request routing."""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = http_client.get(f"{router_url}/api/")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

class TestServiceDiscovery:
    """Test router service discovery functionality."""
    
    @pytest.fixture
    def router_url(self):
        return "http://localhost:59000"
    
    async def test_backend_service_discovery(self, router_url):
        """Test backend service discovery."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{router_url}/health/services/backend")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["service"] == "backend"
            assert "healthy" in data["data"]
    
    async def test_service_health_monitoring(self, router_url):
        """Test service health monitoring."""
        async with httpx.AsyncClient() as client:
            # Check detailed health multiple times
            for i in range(3):
                response = await client.get(f"{router_url}/health/detailed")
                assert response.status_code == 200
                
                data = response.json()
                assert "services" in data["data"]
                
                # Wait between checks
                await asyncio.sleep(1)
```

### Step 3: End-to-End Integration Tests

**File**: `tests/integration/test_e2e_integration.py`
```python
"""
End-to-end integration tests
"""

import pytest
import asyncio
import httpx
import psycopg2
import json
import uuid

class TestEndToEndIntegration:
    """Complete end-to-end integration tests."""
    
    @pytest.fixture(scope="class")
    def services(self):
        return {
            "frontend": "http://localhost:59001",
            "router": "http://localhost:59000", 
            "backend": "http://localhost:59002",
            "pgadmin": "http://localhost:38085"
        }
    
    @pytest.fixture(scope="class")
    def database_config(self):
        return {
            "host": "localhost",
            "port": 5432,
            "database": "autofighter",
            "user": "autofighter", 
            "password": "password"
        }
    
    async def test_all_services_healthy(self, services):
        """Test that all services are running and healthy."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test frontend
            response = await client.get(services["frontend"])
            assert response.status_code == 200
            
            # Test router health
            response = await client.get(f"{services['router']}/health")
            assert response.status_code == 200
            
            # Test backend health
            response = await client.get(f"{services['backend']}/health")
            assert response.status_code == 200
            
            # Test pgAdmin (may take longer to start)
            try:
                response = await client.get(services["pgadmin"])
                # pgAdmin might return various status codes during startup
                assert response.status_code in [200, 302, 401]
            except:
                # pgAdmin might not be fully ready, which is okay for basic test
                pass
    
    async def test_complete_game_flow(self, services):
        """Test complete game flow from frontend through all services."""
        router_url = services["router"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Create game session
            response = await client.post(f"{router_url}/api/game/session")
            assert response.status_code == 201
            
            session_data = response.json()
            session_id = session_data["data"]["session_id"]
            
            # Step 2: Add owned player
            player_id = f"e2e_player_{uuid.uuid4().hex[:8]}"
            player_data = {
                "name": "E2E Test Player",
                "class": "warrior",
                "level": 1
            }
            
            response = await client.post(
                f"{router_url}/api/game/players/{player_id}/own",
                json={"player_data": player_data}
            )
            assert response.status_code == 201
            
            # Step 3: Start game run
            party = {player_id: player_data}
            map_config = {"level": 1, "area": "e2e_test", "difficulty": "normal"}
            
            response = await client.post(
                f"{router_url}/api/game/session/{session_id}/run",
                json={"party": party, "map": map_config}
            )
            assert response.status_code == 201
            
            run_data = response.json()
            run_id = run_data["data"]["run_id"]
            
            # Step 4: Perform gacha roll
            response = await client.post(
                f"{router_url}/api/game/gacha/roll",
                json={"player_id": player_id, "type": "standard"}
            )
            assert response.status_code == 201
            
            gacha_data = response.json()
            assert len(gacha_data["data"]["items"]) > 0
            
            # Step 5: Update upgrade points
            response = await client.post(
                f"{router_url}/api/game/players/{player_id}/upgrades",
                json={
                    "points_delta": 150,
                    "stat_upgrades": {"hp": 15, "atk": 10, "def": 5}
                }
            )
            assert response.status_code == 200
            
            upgrade_data = response.json()
            assert upgrade_data["data"]["points"] == 150
            
            # Step 6: Verify all data is persisted
            # Check run exists
            response = await client.get(
                f"{router_url}/api/game/session/{session_id}/run/{run_id}"
            )
            assert response.status_code == 200
            
            # Check owned players
            response = await client.get(f"{router_url}/api/game/players/owned")
            assert response.status_code == 200
            owned_players = response.json()["data"]["players"]
            assert player_id in owned_players
            
            # Check gacha items
            response = await client.get(f"{router_url}/api/game/gacha/items")
            assert response.status_code == 200
            items = response.json()["data"]["items"]
            assert len(items) > 0
            
            # Check upgrade points
            response = await client.get(
                f"{router_url}/api/game/players/{player_id}/upgrades"
            )
            assert response.status_code == 200
            upgrades = response.json()["data"]
            assert upgrades["points"] == 150
            assert upgrades["hp"] == 15
    
    def test_database_integration(self, database_config):
        """Test database integration and data persistence."""
        conn = psycopg2.connect(**database_config)
        cursor = conn.cursor()
        
        try:
            # Verify data exists from previous tests
            cursor.execute("SELECT COUNT(*) FROM runs")
            runs_count = cursor.fetchone()[0]
            assert runs_count > 0
            
            cursor.execute("SELECT COUNT(*) FROM owned_players") 
            players_count = cursor.fetchone()[0]
            assert players_count > 0
            
            cursor.execute("SELECT COUNT(*) FROM gacha_items")
            items_count = cursor.fetchone()[0]
            assert items_count > 0
            
            # Test data relationships
            cursor.execute("""
                SELECT r.legacy_id, r.party, r.map
                FROM runs r 
                WHERE r.party IS NOT NULL 
                LIMIT 1
            """)
            run_data = cursor.fetchone()
            assert run_data is not None
            
            party = json.loads(run_data[1])
            assert len(party) > 0
            
        finally:
            cursor.close()
            conn.close()
    
    async def test_service_communication_chain(self, services):
        """Test the complete service communication chain."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Frontend -> Router -> Backend -> Database chain
            
            # Start at router (simulating frontend request)
            response = await client.get(f"{services['router']}/health/detailed")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "success"
            
            # Verify router can see backend
            assert "services" in health_data["data"]
            assert "backend" in health_data["data"]["services"]
            backend_healthy = health_data["data"]["services"]["backend"]["healthy"]
            assert backend_healthy is True
            
            # Test actual API flow through chain
            response = await client.post(f"{services['router']}/api/game/session")
            assert response.status_code == 201
            
            # This request went: Router -> Backend -> Database
            session_data = response.json()
            assert session_data["status"] == "success"
            assert "session_id" in session_data["data"]
    
    async def test_error_propagation(self, services):
        """Test error propagation through service chain."""
        async with httpx.AsyncClient() as client:
            # Test invalid request propagation
            response = await client.get(f"{services['router']}/api/invalid/endpoint")
            assert response.status_code == 404
            
            # Test invalid data propagation
            response = await client.post(
                f"{services['router']}/api/game/gacha/roll",
                json={"invalid": "data", "type": "invalid_type"}
            )
            assert response.status_code == 400
            
            error_data = response.json()
            assert error_data["status"] == "error"

@pytest.mark.asyncio
class TestLoadAndStress:
    """Load and stress tests."""
    
    @pytest.fixture
    def router_url(self):
        return "http://localhost:59000"
    
    async def test_concurrent_sessions(self, router_url):
        """Test creating multiple concurrent sessions."""
        async with httpx.AsyncClient() as client:
            # Create 20 concurrent sessions
            tasks = []
            for i in range(20):
                task = client.post(f"{router_url}/api/game/session")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful sessions
            successful = 0
            for response in responses:
                if not isinstance(response, Exception) and response.status_code == 201:
                    successful += 1
            
            # At least 80% should succeed
            assert successful >= 16
    
    async def test_rapid_api_calls(self, router_url):
        """Test rapid API calls."""
        async with httpx.AsyncClient() as client:
            # Make rapid health checks
            tasks = []
            for i in range(50):
                task = client.get(f"{router_url}/health")
                tasks.append(task)
            
            start_time = asyncio.get_event_loop().time()
            responses = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Should complete within reasonable time
            total_time = end_time - start_time
            assert total_time < 10.0  # 50 requests in under 10 seconds
```

### Step 4: Test Configuration and Runner

**File**: `tests/integration/conftest.py`
```python
"""
Integration test configuration
"""

import pytest
import asyncio
import httpx
import time
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running tests."""
    print("\n🔧 Setting up integration test environment...")
    
    # Wait for services to be ready
    max_wait = 60  # seconds
    start_time = time.time()
    
    services = [
        ("Router", "http://localhost:59000/health"),
        ("Backend", "http://localhost:59002/health"),
        ("Database", "localhost:5432")
    ]
    
    async def check_services():
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service_name, url in services[:2]:  # HTTP services
                while time.time() - start_time < max_wait:
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            print(f"✅ {service_name} is ready")
                            break
                    except:
                        pass
                    await asyncio.sleep(2)
                else:
                    raise TimeoutError(f"❌ {service_name} not ready after {max_wait}s")
    
    # Check database separately
    def check_database():
        while time.time() - start_time < max_wait:
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="autofighter",
                    user="autofighter",
                    password="password",
                    connect_timeout=5
                )
                conn.close()
                print("✅ Database is ready")
                return
            except:
                pass
            time.sleep(2)
        raise TimeoutError("❌ Database not ready after {max_wait}s")
    
    # Run checks
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_services())
    check_database()
    
    print("🎉 All services are ready for testing!")
    
    yield
    
    print("\n🧹 Cleaning up test environment...")

@pytest.fixture(scope="session")
def test_database():
    """Setup test database with clean state."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autofighter",
        user="autofighter", 
        password="password"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    yield conn
    
    # Cleanup test data
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gacha_rolls WHERE player_id LIKE 'test_%'")
    cursor.execute("DELETE FROM gacha_items WHERE legacy_id LIKE 'test_%'")
    cursor.execute("DELETE FROM upgrade_points WHERE player_id LIKE 'test_%'")
    cursor.execute("DELETE FROM owned_players WHERE legacy_id LIKE 'test_%'")
    cursor.execute("DELETE FROM runs WHERE legacy_id LIKE 'test_%'")
    cursor.close()
    
    conn.close()

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
```

**File**: `tests/integration/pytest.ini`
```ini
[tool:pytest]
testpaths = tests/integration
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers = 
    integration: Integration tests
    slow: Slow running tests
asyncio_mode = auto
```

### Step 5: Test Runner Script

**File**: `scripts/run-integration-tests.sh`
```bash
#!/bin/bash
set -e

echo "=== AutoFighter Integration Tests ==="
echo ""

# Check if services are running
echo "🔍 Checking if services are running..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Services are not running. Please start them first:"
    echo "   ./scripts/compose-dev.sh up"
    exit 1
fi

echo "✅ Services are running"
echo ""

# Install test dependencies
echo "📦 Installing test dependencies..."
cd tests/integration
python -m pip install pytest pytest-asyncio httpx psycopg2-binary requests

# Run integration tests
echo ""
echo "🧪 Running integration tests..."
echo ""

# Run different test categories
echo ">>> Backend Integration Tests"
pytest test_backend_integration.py -v

echo ""
echo ">>> Router Integration Tests" 
pytest test_router_integration.py -v

echo ""
echo ">>> End-to-End Integration Tests"
pytest test_e2e_integration.py -v

echo ""
echo "🎉 All integration tests completed!"

# Generate test report
echo ""
echo "📊 Test Summary:"
pytest --collect-only -q | grep "test session starts"
```

## Validation Criteria

### Success Criteria
1. **Service Communication**: All services communicate correctly through the architecture
2. **API Functionality**: All API endpoints work as expected
3. **Data Persistence**: Data is properly stored and retrieved from database
4. **Error Handling**: Errors are properly handled and propagated
5. **Performance**: System handles concurrent requests appropriately

### Validation Commands
```bash
# Start services
./scripts/compose-dev.sh up

# Wait for services to be ready
sleep 30

# Run integration tests
chmod +x scripts/run-integration-tests.sh
./scripts/run-integration-tests.sh

# Run specific test categories
cd tests/integration
pytest test_backend_integration.py -v
pytest test_router_integration.py -v
pytest test_e2e_integration.py -v

# Run performance tests only
pytest -k "performance" -v
```

### Expected Results
- All integration tests pass successfully
- Service communication works correctly
- Database operations complete successfully
- API responses are properly formatted
- Error handling works as expected
- Performance tests meet timing requirements

## Notes

- Tests require all services to be running via Docker Compose
- Database tests use real PostgreSQL instance
- Performance tests validate response times and concurrency
- Error tests ensure proper error propagation through service chain
- End-to-end tests validate complete user workflows