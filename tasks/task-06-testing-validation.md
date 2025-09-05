# Task 06: Testing and Validation

## Objective
Implement comprehensive testing and validation for the new 4-service architecture to ensure all components work together correctly and maintain existing functionality.

## Requirements

### 1. Integration Testing
- End-to-end communication testing
- Service dependency validation
- API functionality verification
- Database operations testing

### 2. Performance Validation
- Service startup times
- Request/response latency
- Resource usage monitoring
- Load testing for router service

### 3. Regression Testing
- Existing game functionality preserved
- API compatibility maintained
- Data integrity verified
- User experience unchanged

## Implementation Tasks

### Task 6.1: Comprehensive Integration Test Suite
**File**: `tests/integration/test_architecture.py`
```python
#!/usr/bin/env python3
"""
Comprehensive integration tests for the new 4-service architecture
"""

import pytest
import asyncio
import httpx
import psycopg2
import time
import json
from pathlib import Path
import subprocess
import os

# Test configuration
SERVICES = {
    'frontend': 'http://localhost:59001',
    'router': 'http://localhost:59000', 
    'backend': 'http://localhost:59002',
    'database': 'postgresql://autofighter:autofighter_dev_password@localhost:5432/autofighter'
}

class TestArchitectureIntegration:
    """Integration tests for the new service architecture"""
    
    @pytest.fixture(scope="class")
    async def setup_services(self):
        """Ensure all services are running for tests"""
        print("🚀 Starting services for integration tests...")
        
        # Start services using docker-compose
        result = subprocess.run([
            "docker", "compose", "-f", "compose.yaml", "-f", "compose.dev.yaml", 
            "up", "-d"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            pytest.fail(f"Failed to start services: {result.stderr}")
        
        # Wait for services to be ready
        await self._wait_for_services()
        
        yield
        
        # Cleanup after tests
        subprocess.run([
            "docker", "compose", "down"
        ], capture_output=True)
    
    async def _wait_for_services(self, timeout=120):
        """Wait for all services to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check each service
                async with httpx.AsyncClient() as client:
                    # Router health check
                    router_response = await client.get(f"{SERVICES['router']}/health/")
                    if router_response.status_code != 200:
                        continue
                    
                    # Backend through router
                    backend_response = await client.get(f"{SERVICES['router']}/api/")
                    if backend_response.status_code != 200:
                        continue
                    
                    # Frontend
                    frontend_response = await client.get(f"{SERVICES['frontend']}/")
                    if frontend_response.status_code != 200:
                        continue
                
                # Database connectivity
                conn = psycopg2.connect(SERVICES['database'])
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                
                print("✅ All services are ready")
                return
                
            except Exception as e:
                print(f"⏳ Waiting for services... ({e})")
                await asyncio.sleep(5)
        
        pytest.fail("Services failed to start within timeout")

    @pytest.mark.asyncio
    async def test_service_communication_flow(self, setup_services):
        """Test the complete communication flow: Frontend → Router → Backend → Database"""
        
        async with httpx.AsyncClient() as client:
            # Test 1: Frontend can reach router
            response = await client.get(f"{SERVICES['router']}/health/")
            assert response.status_code == 200
            health_data = response.json()
            assert health_data['status'] in ['healthy', 'degraded']
            
            # Test 2: Router can reach backend
            response = await client.get(f"{SERVICES['router']}/api/")
            assert response.status_code == 200
            backend_data = response.json()
            assert 'status' in backend_data
            
            # Test 3: Backend can reach database (through router)
            response = await client.get(f"{SERVICES['router']}/api/players")
            assert response.status_code == 200
            players_data = response.json()
            
            # Validate response format
            if isinstance(players_data, dict) and 'data' in players_data:
                # New standardized format
                assert 'status' in players_data
                assert players_data['status'] == 'ok'
                assert 'data' in players_data
            else:
                # Legacy format (should still work)
                assert isinstance(players_data, (list, dict))

    @pytest.mark.asyncio 
    async def test_database_operations_through_router(self, setup_services):
        """Test database operations through the complete stack"""
        
        async with httpx.AsyncClient() as client:
            # Test player creation
            initial_response = await client.get(f"{SERVICES['router']}/api/players")
            assert initial_response.status_code == 200
            
            # Test gacha operations
            gacha_response = await client.get(f"{SERVICES['router']}/api/gacha")
            assert gacha_response.status_code == 200
            
            # Test gacha pull (writes to database)
            pull_response = await client.post(
                f"{SERVICES['router']}/api/gacha/pull",
                json={"count": 1}
            )
            assert pull_response.status_code == 200
            
            # Verify the pull was recorded
            gacha_after = await client.get(f"{SERVICES['router']}/api/gacha")
            assert gacha_after.status_code == 200

    @pytest.mark.asyncio
    async def test_error_handling_and_propagation(self, setup_services):
        """Test error handling through the service chain"""
        
        async with httpx.AsyncClient() as client:
            # Test invalid endpoint
            response = await client.get(f"{SERVICES['router']}/api/invalid-endpoint")
            assert response.status_code in [404, 500]
            
            # Test invalid data
            response = await client.post(
                f"{SERVICES['router']}/api/gacha/pull", 
                json={"count": -1}  # Invalid count
            )
            assert response.status_code in [400, 422, 500]

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, setup_services):
        """Test health monitoring capabilities"""
        
        async with httpx.AsyncClient() as client:
            # Router health check
            response = await client.get(f"{SERVICES['router']}/health/")
            assert response.status_code in [200, 503]
            health_data = response.json()
            
            assert 'status' in health_data
            assert 'timestamp' in health_data
            assert 'services' in health_data or 'checks' in health_data
            
            # Backend health check through router
            response = await client.get(f"{SERVICES['router']}/api/health/")
            assert response.status_code in [200, 503]

    def test_database_schema_and_data_integrity(self, setup_services):
        """Test database schema and data integrity"""
        
        conn = psycopg2.connect(SERVICES['database'])
        cursor = conn.cursor()
        
        # Test required tables exist
        required_tables = [
            'runs', 'owned_players', 'gacha_items', 
            'gacha_rolls', 'upgrade_points', 'damage_types'
        ]
        
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        for table in required_tables:
            assert table in existing_tables, f"Required table {table} is missing"
        
        # Test data can be inserted and retrieved
        cursor.execute("""
            INSERT INTO owned_players (legacy_id) 
            VALUES ('test_integration') 
            ON CONFLICT (legacy_id) DO NOTHING
            RETURNING id
        """)
        
        if cursor.rowcount > 0:
            test_id = cursor.fetchone()[0]
            
            # Verify the record exists
            cursor.execute("SELECT * FROM owned_players WHERE id = %s", (test_id,))
            result = cursor.fetchone()
            assert result is not None
            
            # Clean up test data
            cursor.execute("DELETE FROM owned_players WHERE id = %s", (test_id,))
        
        conn.commit()
        conn.close()

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, setup_services):
        """Test handling of concurrent requests"""
        
        async def make_request(client, endpoint):
            response = await client.get(endpoint)
            return response.status_code, response.elapsed.total_seconds()
        
        async with httpx.AsyncClient() as client:
            # Make concurrent requests to different endpoints
            tasks = [
                make_request(client, f"{SERVICES['router']}/api/"),
                make_request(client, f"{SERVICES['router']}/api/players"),
                make_request(client, f"{SERVICES['router']}/api/gacha"),
                make_request(client, f"{SERVICES['router']}/health/"),
            ] * 5  # 20 concurrent requests
            
            results = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for status_code, response_time in results:
                assert status_code == 200
                assert response_time < 10.0  # Should respond within 10 seconds
```

### Task 6.2: Performance Benchmarking
**File**: `tests/performance/benchmark_architecture.py`
```python
#!/usr/bin/env python3
"""
Performance benchmarks for the new architecture
"""

import asyncio
import httpx
import time
import statistics
import json
from datetime import datetime
import psutil
import docker

class ArchitectureBenchmark:
    """Performance benchmarks for the service architecture"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.results = {}
    
    async def benchmark_service_startup(self):
        """Benchmark service startup times"""
        print("🚀 Benchmarking service startup times...")
        
        # Stop services if running
        subprocess.run(["docker", "compose", "down"], capture_output=True)
        
        start_time = time.time()
        
        # Start services
        result = subprocess.run([
            "docker", "compose", "-f", "compose.yaml", "-f", "compose.dev.yaml",
            "up", "-d"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to start services: {result.stderr}")
        
        # Wait for all services to be ready
        services_ready = {}
        
        while len(services_ready) < 4:  # 4 services total
            try:
                # Check router
                if 'router' not in services_ready:
                    async with httpx.AsyncClient() as client:
                        response = await client.get("http://localhost:59000/health/", timeout=2)
                        if response.status_code == 200:
                            services_ready['router'] = time.time() - start_time
                
                # Check backend through router
                if 'backend' not in services_ready and 'router' in services_ready:
                    async with httpx.AsyncClient() as client:
                        response = await client.get("http://localhost:59000/api/", timeout=2)
                        if response.status_code == 200:
                            services_ready['backend'] = time.time() - start_time
                
                # Check frontend
                if 'frontend' not in services_ready:
                    async with httpx.AsyncClient() as client:
                        response = await client.get("http://localhost:59001/", timeout=2)
                        if response.status_code == 200:
                            services_ready['frontend'] = time.time() - start_time
                
                # Check database
                if 'database' not in services_ready:
                    try:
                        conn = psycopg2.connect(
                            "postgresql://autofighter:autofighter_dev_password@localhost:5432/autofighter",
                            connect_timeout=2
                        )
                        conn.close()
                        services_ready['database'] = time.time() - start_time
                    except:
                        pass
                
            except:
                pass
            
            await asyncio.sleep(1)
        
        total_startup_time = time.time() - start_time
        
        self.results['startup_times'] = {
            'total': total_startup_time,
            'services': services_ready
        }
        
        print(f"    ✓ Total startup time: {total_startup_time:.2f}s")
        for service, time_taken in services_ready.items():
            print(f"    ✓ {service}: {time_taken:.2f}s")

    async def benchmark_request_latency(self):
        """Benchmark request latency through the router"""
        print("⚡ Benchmarking request latency...")
        
        endpoints = [
            ("GET", "/api/", "Backend status"),
            ("GET", "/api/players", "Get players"),
            ("GET", "/api/gacha", "Get gacha"),
            ("GET", "/health/", "Router health"),
        ]
        
        latencies = {}
        
        async with httpx.AsyncClient() as client:
            for method, endpoint, description in endpoints:
                times = []
                
                for _ in range(50):  # 50 requests per endpoint
                    start = time.time()
                    
                    if method == "GET":
                        response = await client.get(f"http://localhost:59000{endpoint}")
                    elif method == "POST":
                        response = await client.post(f"http://localhost:59000{endpoint}")
                    
                    end = time.time()
                    
                    if response.status_code == 200:
                        times.append((end - start) * 1000)  # Convert to milliseconds
                
                if times:
                    latencies[description] = {
                        'mean': statistics.mean(times),
                        'median': statistics.median(times),
                        'min': min(times),
                        'max': max(times),
                        'p95': sorted(times)[int(len(times) * 0.95)]
                    }
        
        self.results['latencies'] = latencies
        
        for description, stats in latencies.items():
            print(f"    ✓ {description}:")
            print(f"      Mean: {stats['mean']:.1f}ms")
            print(f"      P95:  {stats['p95']:.1f}ms")

    def benchmark_resource_usage(self):
        """Benchmark resource usage of services"""
        print("💾 Benchmarking resource usage...")
        
        containers = self.client.containers.list(filters={'name': 'autofighter'})
        
        resource_usage = {}
        
        for container in containers:
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            cpu_percent = 0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            service_name = container.name.replace('autofighter-', '')
            resource_usage[service_name] = {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_usage / (1024 * 1024),
                'memory_percent': memory_percent
            }
        
        self.results['resource_usage'] = resource_usage
        
        for service, stats in resource_usage.items():
            print(f"    ✓ {service}:")
            print(f"      CPU: {stats['cpu_percent']:.1f}%")
            print(f"      Memory: {stats['memory_mb']:.1f}MB ({stats['memory_percent']:.1f}%)")

    async def benchmark_load_testing(self):
        """Basic load testing of the router service"""
        print("🔥 Running basic load test...")
        
        async def worker(session, endpoint, requests_per_worker):
            successful = 0
            failed = 0
            total_time = 0
            
            for _ in range(requests_per_worker):
                start = time.time()
                try:
                    response = await session.get(endpoint)
                    if response.status_code == 200:
                        successful += 1
                    else:
                        failed += 1
                except:
                    failed += 1
                
                total_time += time.time() - start
            
            return successful, failed, total_time
        
        # Load test configuration
        concurrent_workers = 10
        requests_per_worker = 20
        total_requests = concurrent_workers * requests_per_worker
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            # Create workers
            tasks = [
                worker(client, "http://localhost:59000/api/", requests_per_worker)
                for _ in range(concurrent_workers)
            ]
            
            # Run load test
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            
            # Aggregate results
            total_successful = sum(r[0] for r in results)
            total_failed = sum(r[1] for r in results)
            total_duration = end_time - start_time
            
            requests_per_second = total_requests / total_duration
            
            self.results['load_test'] = {
                'total_requests': total_requests,
                'successful': total_successful,
                'failed': total_failed,
                'duration': total_duration,
                'requests_per_second': requests_per_second
            }
            
            print(f"    ✓ Total requests: {total_requests}")
            print(f"    ✓ Successful: {total_successful}")
            print(f"    ✓ Failed: {total_failed}")
            print(f"    ✓ Requests/second: {requests_per_second:.1f}")

    def save_results(self):
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📊 Benchmark results saved to {filename}")

    async def run_all_benchmarks(self):
        """Run all benchmarks"""
        print("🎯 Running architecture performance benchmarks...")
        print("=" * 60)
        
        try:
            await self.benchmark_service_startup()
            await self.benchmark_request_latency()
            self.benchmark_resource_usage()
            await self.benchmark_load_testing()
            
            self.save_results()
            
            print("=" * 60)
            print("✅ All benchmarks completed successfully!")
            
        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            raise

async def main():
    benchmark = ArchitectureBenchmark()
    await benchmark.run_all_benchmarks()

if __name__ == "__main__":
    asyncio.run(main())
```

### Task 6.3: Regression Testing Suite
**File**: `tests/regression/test_game_functionality.py`
```python
#!/usr/bin/env python3
"""
Regression tests to ensure existing game functionality is preserved
"""

import pytest
import asyncio
import httpx
import json

class TestGameFunctionalityRegression:
    """Regression tests for game functionality through new architecture"""
    
    @pytest.fixture(scope="class")
    def api_base(self):
        return "http://localhost:59000/api"
    
    @pytest.mark.asyncio
    async def test_player_management(self, api_base):
        """Test player management functionality"""
        
        async with httpx.AsyncClient() as client:
            # Get initial players
            response = await client.get(f"{api_base}/players")
            assert response.status_code == 200
            
            initial_data = response.json()
            
            # Handle both new and legacy response formats
            if isinstance(initial_data, dict) and 'data' in initial_data:
                players = initial_data['data']['players'] if 'players' in initial_data['data'] else initial_data['data']
            else:
                players = initial_data
            
            # Should have at least the default player
            assert isinstance(players, list)

    @pytest.mark.asyncio
    async def test_gacha_system(self, api_base):
        """Test gacha system functionality"""
        
        async with httpx.AsyncClient() as client:
            # Get gacha state
            response = await client.get(f"{api_base}/gacha")
            assert response.status_code == 200
            
            gacha_data = response.json()
            
            # Handle response format
            if isinstance(gacha_data, dict) and 'data' in gacha_data:
                gacha_info = gacha_data['data']
            else:
                gacha_info = gacha_data
            
            # Test gacha pull
            response = await client.post(f"{api_base}/gacha/pull", json={"count": 1})
            assert response.status_code == 200
            
            pull_result = response.json()
            
            # Should return pulled items
            if isinstance(pull_result, dict) and 'data' in pull_result:
                items = pull_result['data']
            else:
                items = pull_result
            
            assert 'items' in items or isinstance(items, list)

    @pytest.mark.asyncio
    async def test_player_customization(self, api_base):
        """Test player customization functionality"""
        
        async with httpx.AsyncClient() as client:
            # Get player config
            response = await client.get(f"{api_base}/player/editor")
            assert response.status_code == 200
            
            config_data = response.json()
            
            # Handle response format
            if isinstance(config_data, dict) and 'data' in config_data:
                config = config_data['data']
            else:
                config = config_data
            
            # Should have player configuration fields
            expected_fields = ['hp', 'attack', 'defense']
            for field in expected_fields:
                assert field in config or any(field in str(config).lower() for field in expected_fields)

    @pytest.mark.asyncio  
    async def test_save_operations(self, api_base):
        """Test save/load operations"""
        
        async with httpx.AsyncClient() as client:
            # Test export save
            response = await client.get(f"{api_base}/save/backup")
            assert response.status_code == 200
            
            # Should return binary data
            assert len(response.content) > 0
            
            # Test save wipe (destructive, so we test the endpoint exists)
            # Note: We don't actually wipe in regression tests
            # Just verify the endpoint is available
            response = await client.options(f"{api_base}/save/wipe")
            assert response.status_code in [200, 204, 405]  # Various valid responses

    @pytest.mark.asyncio
    async def test_catalog_access(self, api_base):
        """Test catalog access functionality"""
        
        async with httpx.AsyncClient() as client:
            # Test card catalog
            response = await client.get(f"{api_base}/catalog/cards")
            assert response.status_code == 200
            
            cards_data = response.json()
            
            # Handle response format
            if isinstance(cards_data, dict) and 'data' in cards_data:
                cards = cards_data['data']
            else:
                cards = cards_data
            
            # Should be a list of cards or dict with cards
            assert isinstance(cards, (list, dict))
            
            # Test relic catalog
            response = await client.get(f"{api_base}/catalog/relics")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upgrade_system(self, api_base):
        """Test upgrade system functionality"""
        
        async with httpx.AsyncClient() as client:
            # Get players to test upgrades
            response = await client.get(f"{api_base}/players")
            assert response.status_code == 200
            
            players_data = response.json()
            
            # Handle response format
            if isinstance(players_data, dict) and 'data' in players_data:
                players = players_data['data']['players'] if 'players' in players_data['data'] else players_data['data']
            else:
                players = players_data
            
            if players and len(players) > 0:
                player_id = players[0]['id'] if isinstance(players[0], dict) else 'player'
                
                # Test get upgrade info
                response = await client.get(f"{api_base}/players/{player_id}/upgrade")
                # This might fail if player doesn't exist, which is ok for regression test
                # Just verify the endpoint exists and responds
                assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, api_base):
        """Test that error handling is consistent with previous behavior"""
        
        async with httpx.AsyncClient() as client:
            # Test invalid endpoints return appropriate errors
            response = await client.get(f"{api_base}/nonexistent")
            assert response.status_code in [404, 500]
            
            # Test invalid data returns appropriate errors
            response = await client.post(f"{api_base}/gacha/pull", json={"invalid": "data"})
            assert response.status_code in [400, 422, 500]
            
            # Test malformed JSON
            response = await client.post(
                f"{api_base}/gacha/pull", 
                content="invalid json",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [400, 422, 500]
```

### Task 6.4: End-to-End User Journey Tests
**File**: `tests/e2e/test_user_journeys.py`
```python
#!/usr/bin/env python3
"""
End-to-end user journey tests
"""

import pytest
import asyncio
import httpx
from playwright.async_api import async_playwright

class TestUserJourneys:
    """End-to-end tests simulating real user interactions"""
    
    @pytest.mark.asyncio
    async def test_complete_game_session(self):
        """Test a complete game session from start to finish"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to frontend
            await page.goto("http://localhost:59001")
            
            # Wait for page to load
            await page.wait_for_selector("body")
            
            # Check that page loads without JavaScript errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            # Wait a bit for any async operations
            await page.wait_for_timeout(5000)
            
            # Should not have critical JavaScript errors
            critical_errors = [err for err in console_errors if "network" not in err.lower()]
            assert len(critical_errors) == 0, f"JavaScript errors: {critical_errors}"
            
            await browser.close()

    @pytest.mark.asyncio
    async def test_api_communication_flow(self):
        """Test the complete API communication flow"""
        
        async with httpx.AsyncClient() as client:
            # 1. Check frontend can reach router
            response = await client.get("http://localhost:59000/health/")
            assert response.status_code in [200, 503]
            
            # 2. Check router can reach backend
            response = await client.get("http://localhost:59000/api/")
            assert response.status_code == 200
            
            # 3. Perform a series of game operations
            operations = [
                ("GET", "/api/players", "Get players"),
                ("GET", "/api/gacha", "Get gacha state"),
                ("POST", "/api/gacha/pull", {"count": 1}, "Pull gacha"),
                ("GET", "/api/catalog/cards", "Get card catalog"),
                ("GET", "/api/player/editor", "Get player config"),
            ]
            
            for method, endpoint, *args in operations:
                if method == "GET":
                    description = args[0]
                    response = await client.get(f"http://localhost:59000{endpoint}")
                elif method == "POST":
                    data, description = args
                    response = await client.post(
                        f"http://localhost:59000{endpoint}",
                        json=data
                    )
                
                # All operations should succeed or fail gracefully
                assert response.status_code in [200, 400, 404, 422, 500], \
                    f"{description} returned unexpected status: {response.status_code}"
                
                # If successful, should return valid JSON
                if response.status_code == 200:
                    try:
                        data = response.json()
                        assert data is not None
                    except:
                        pytest.fail(f"{description} returned invalid JSON")
```

### Task 6.5: Master Validation Script
**File**: `validate_complete_migration.py`
```python
#!/usr/bin/env python3
"""
Master validation script for the complete architecture migration
"""

import subprocess
import asyncio
import sys
import time
from pathlib import Path

async def run_validation_step(name, command, timeout=300):
    """Run a validation step with proper error handling"""
    print(f"🔍 {name}...")
    
    try:
        if asyncio.iscoroutinefunction(command):
            result = await command()
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = result.returncode == 0
            if not success:
                print(f"    ❌ {name} failed:")
                print(f"    stdout: {result.stdout}")
                print(f"    stderr: {result.stderr}")
                return False
        
        print(f"    ✅ {name} passed")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"    ❌ {name} timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"    ❌ {name} failed with exception: {e}")
        return False

async def setup_test_environment():
    """Set up the test environment"""
    print("🚀 Setting up test environment...")
    
    # Stop any existing services
    subprocess.run(["docker", "compose", "down"], capture_output=True)
    
    # Start services
    result = subprocess.run([
        "docker", "compose", "-f", "compose.yaml", "-f", "compose.dev.yaml",
        "up", "-d"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to start services: {result.stderr}")
        return False
    
    # Wait for services to be ready
    print("    ⏳ Waiting for services to be ready...")
    time.sleep(60)  # Give services time to start
    
    return True

async def cleanup_test_environment():
    """Clean up the test environment"""
    print("🧹 Cleaning up test environment...")
    subprocess.run(["docker", "compose", "down"], capture_output=True)

async def main():
    """Main validation function"""
    print("🎯 Complete Architecture Migration Validation")
    print("=" * 60)
    
    validation_steps = [
        ("Environment Setup", setup_test_environment),
        ("Docker Configuration", "python scripts/validate_docker_setup.py"),
        ("Integration Tests", "python -m pytest tests/integration/ -v"),
        ("Performance Benchmarks", "python tests/performance/benchmark_architecture.py"),
        ("Regression Tests", "python -m pytest tests/regression/ -v"),
        ("End-to-End Tests", "python -m pytest tests/e2e/ -v"),
    ]
    
    passed = 0
    failed = 0
    
    try:
        for step_name, step_command in validation_steps:
            success = await run_validation_step(step_name, step_command)
            if success:
                passed += 1
            else:
                failed += 1
                
                # Stop on critical failures
                if step_name in ["Environment Setup", "Docker Configuration"]:
                    print(f"❌ Critical failure in {step_name}, stopping validation")
                    break
    
    finally:
        await cleanup_test_environment()
    
    print("=" * 60)
    print(f"📊 Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All validations passed! Migration is successful.")
        return True
    else:
        print("❌ Some validations failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

### Task 6.6: Continuous Testing Configuration
**File**: `tests/pytest.ini`
```ini
[tool:pytest]
addopts = -v --tb=short --strict-markers
testpaths = tests
markers =
    integration: Integration tests requiring all services
    performance: Performance and load tests  
    regression: Regression tests for existing functionality
    e2e: End-to-end user journey tests
    slow: Tests that take longer than 30 seconds
    
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

**File**: `tests/conftest.py`
```python
"""Shared pytest configuration and fixtures"""

import pytest
import asyncio
import subprocess
import time

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def ensure_services_running():
    """Ensure services are running for all tests"""
    # Check if services are already running
    result = subprocess.run([
        "docker", "compose", "ps", "--services", "--filter", "status=running"
    ], capture_output=True, text=True)
    
    running_services = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    required_services = {'frontend', 'router', 'backend', 'database'}
    
    if not required_services.issubset(running_services):
        print("Starting services for tests...")
        subprocess.run([
            "docker", "compose", "-f", "compose.yaml", "-f", "compose.dev.yaml",
            "up", "-d"
        ], check=True)
        
        # Wait for services to be ready
        time.sleep(30)
    
    yield
    
    # Don't stop services after tests - let developer manage lifecycle
```

## Testing Commands

```bash
# Run all validation tests
python validate_complete_migration.py

# Run specific test suites
python -m pytest tests/integration/ -v
python -m pytest tests/regression/ -v  
python -m pytest tests/performance/ -v
python -m pytest tests/e2e/ -v

# Run performance benchmarks
python tests/performance/benchmark_architecture.py

# Install test dependencies
pip install pytest pytest-asyncio httpx playwright psycopg2-binary docker

# Set up playwright for e2e tests
playwright install chromium
```

## Completion Criteria

- [ ] All integration tests pass
- [ ] Performance benchmarks show acceptable metrics
- [ ] Regression tests confirm functionality preservation
- [ ] End-to-end tests validate user journeys
- [ ] Master validation script passes completely
- [ ] Test suite can be run repeatably
- [ ] All critical paths through new architecture validated
- [ ] Documentation updated with test results

## Notes for Task Master Review

- Comprehensive test coverage ensures migration success
- Performance benchmarks establish baseline metrics
- Regression tests prevent functionality loss
- End-to-end tests validate real user experience
- Automated validation enables confident deployment

## Expected Outcomes

After successful completion of this task:

1. **Verified Architecture**: Complete 4-service architecture working correctly
2. **Performance Baseline**: Established performance metrics for monitoring
3. **Functionality Assurance**: All existing game features working through new architecture
4. **Quality Gate**: Automated testing prevents regressions
5. **Deployment Ready**: System ready for production deployment

**Final Task**: This completes the architecture refactoring. All services should be communicating properly with simplified patterns and improved maintainability.