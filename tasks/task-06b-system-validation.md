# Task 6B: System Validation

## Overview

This task implements comprehensive system validation including end-to-end testing, performance validation, monitoring setup, and deployment verification to ensure the complete architecture works reliably in production scenarios.

## Goals

- Implement end-to-end system validation tests
- Create performance benchmarking and monitoring
- Set up automated health monitoring and alerting
- Validate deployment and scaling scenarios
- Create system documentation and runbooks

## Prerequisites

- Task 6A (Integration Tests) must be completed
- All services deployed and running
- Monitoring tools and test frameworks available

## Implementation

### Step 1: End-to-End System Tests

**File**: `tests/system/test_system_validation.py`
```python
"""
Complete system validation tests
"""

import pytest
import asyncio
import httpx
import psycopg2
import json
import time
import uuid
import subprocess
import docker
from typing import Dict, List, Any
import statistics

class TestSystemValidation:
    """Complete system validation and reliability tests."""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    def system_endpoints(self):
        return {
            "frontend": "http://localhost:59001",
            "router": "http://localhost:59000",
            "backend": "http://localhost:59002", 
            "pgadmin": "http://localhost:38085",
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "autofighter",
                "user": "autofighter",
                "password": "password"
            }
        }
    
    async def test_complete_user_journey(self, system_endpoints):
        """Test complete user journey from frontend to database."""
        router_url = system_endpoints["router"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: User opens application (frontend health)
            response = await client.get(system_endpoints["frontend"])
            assert response.status_code == 200
            print("✅ Frontend accessible")
            
            # Step 2: Frontend checks router health
            response = await client.get(f"{router_url}/health")
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "success"
            print("✅ Router health check passed")
            
            # Step 3: User creates game session
            response = await client.post(f"{router_url}/api/game/session")
            assert response.status_code == 201
            session_data = response.json()
            session_id = session_data["data"]["session_id"]
            print(f"✅ Game session created: {session_id[:8]}...")
            
            # Step 4: User adds owned players
            players = [
                {"id": f"warrior_{uuid.uuid4().hex[:8]}", "class": "warrior"},
                {"id": f"mage_{uuid.uuid4().hex[:8]}", "class": "mage"},
                {"id": f"archer_{uuid.uuid4().hex[:8]}", "class": "archer"}
            ]
            
            for player in players:
                response = await client.post(
                    f"{router_url}/api/game/players/{player['id']}/own",
                    json={"player_data": {"class": player["class"], "level": 1}}
                )
                assert response.status_code == 201
            print(f"✅ Added {len(players)} players to collection")
            
            # Step 5: User performs multiple gacha rolls
            gacha_results = []
            for i in range(3):
                response = await client.post(
                    f"{router_url}/api/game/gacha/roll",
                    json={"player_id": players[0]["id"], "type": "standard"}
                )
                assert response.status_code == 201
                gacha_data = response.json()
                gacha_results.append(gacha_data["data"])
            print(f"✅ Performed {len(gacha_results)} gacha rolls")
            
            # Step 6: User starts multiple game runs
            runs = []
            for i, player in enumerate(players):
                party = {player["id"]: {"class": player["class"], "level": 1}}
                map_config = {"level": i + 1, "area": f"area_{i + 1}"}
                
                response = await client.post(
                    f"{router_url}/api/game/session/{session_id}/run",
                    json={"party": party, "map": map_config}
                )
                assert response.status_code == 201
                run_data = response.json()
                runs.append(run_data["data"])
            print(f"✅ Created {len(runs)} game runs")
            
            # Step 7: User upgrades players
            for player in players:
                response = await client.post(
                    f"{router_url}/api/game/players/{player['id']}/upgrades",
                    json={
                        "points_delta": 200,
                        "stat_upgrades": {
                            "hp": 20, "atk": 15, "def": 10,
                            "crit_rate": 5, "crit_damage": 8
                        }
                    }
                )
                assert response.status_code == 200
            print(f"✅ Upgraded {len(players)} players")
            
            # Step 8: Verify all data persisted
            # Check owned players
            response = await client.get(f"{router_url}/api/game/players/owned")
            assert response.status_code == 200
            owned_data = response.json()
            for player in players:
                assert player["id"] in owned_data["data"]["players"]
            
            # Check recent runs
            response = await client.get(f"{router_url}/api/game/runs?page=1&page_size=10")
            assert response.status_code == 200
            runs_data = response.json()
            assert len(runs_data["data"]) >= len(runs)
            
            # Check gacha items
            response = await client.get(f"{router_url}/api/game/gacha/items?limit=20")
            assert response.status_code == 200
            items_data = response.json()
            total_items = sum(len(roll["items"]) for roll in gacha_results)
            assert len(items_data["data"]["items"]) >= total_items
            
            print("✅ All user data properly persisted")
            print(f"🎉 Complete user journey test passed!")
    
    def test_database_data_integrity(self, system_endpoints):
        """Validate database data integrity and relationships."""
        db_config = system_endpoints["database"]
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        try:
            # Test data consistency
            cursor.execute("SELECT COUNT(*) FROM runs")
            runs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM owned_players")
            players_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM gacha_items")
            items_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM gacha_rolls")
            rolls_count = cursor.fetchone()[0]
            
            print(f"📊 Database Stats:")
            print(f"   Runs: {runs_count}")
            print(f"   Players: {players_count}")
            print(f"   Gacha Items: {items_count}")
            print(f"   Gacha Rolls: {rolls_count}")
            
            # Test data relationships
            cursor.execute("""
                SELECT COUNT(*) FROM gacha_rolls gr
                JOIN gacha_items gi ON gi.legacy_id = ANY(
                    SELECT jsonb_array_elements_text(gr.items::jsonb)
                )
            """)
            linked_items = cursor.fetchone()[0]
            print(f"   Linked Items: {linked_items}")
            
            # Test data validity
            cursor.execute("""
                SELECT COUNT(*) FROM runs 
                WHERE party IS NOT NULL 
                AND map IS NOT NULL
                AND created_at IS NOT NULL
            """)
            valid_runs = cursor.fetchone()[0]
            assert valid_runs == runs_count
            
            cursor.execute("""
                SELECT COUNT(*) FROM owned_players
                WHERE legacy_id IS NOT NULL
                AND created_at IS NOT NULL
            """)
            valid_players = cursor.fetchone()[0]
            assert valid_players == players_count
            
            print("✅ Database integrity validation passed")
            
        finally:
            cursor.close()
            conn.close()
    
    async def test_system_resilience(self, docker_client, system_endpoints):
        """Test system resilience and recovery."""
        router_url = system_endpoints["router"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: System handles backend restart
            print("🔄 Testing backend restart resilience...")
            
            # Stop backend
            docker_client.containers.get("autofighter_backend").restart()
            
            # Wait for restart
            await asyncio.sleep(10)
            
            # Verify system recovers
            max_retries = 10
            for i in range(max_retries):
                try:
                    response = await client.get(f"{router_url}/health/detailed")
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data["data"]["services"]["backend"]["healthy"]:
                            print("✅ Backend restart recovery successful")
                            break
                except:
                    pass
                await asyncio.sleep(3)
            else:
                pytest.fail("Backend did not recover after restart")
            
            # Test 2: System handles router restart
            print("🔄 Testing router restart resilience...")
            
            docker_client.containers.get("autofighter_router").restart()
            await asyncio.sleep(5)
            
            # Verify router recovers
            for i in range(max_retries):
                try:
                    response = await client.get(f"{router_url}/health")
                    if response.status_code == 200:
                        print("✅ Router restart recovery successful")
                        break
                except:
                    pass
                await asyncio.sleep(2)
            else:
                pytest.fail("Router did not recover after restart")
    
    async def test_concurrent_load_handling(self, system_endpoints):
        """Test system under concurrent load."""
        router_url = system_endpoints["router"]
        
        async def create_session_and_run():
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    # Create session
                    response = await client.post(f"{router_url}/api/game/session")
                    if response.status_code != 201:
                        return False
                    
                    session_id = response.json()["data"]["session_id"]
                    
                    # Start run
                    party = {"test_player": {"name": "Load Test", "level": 1}}
                    map_config = {"level": 1, "area": "load_test"}
                    
                    response = await client.post(
                        f"{router_url}/api/game/session/{session_id}/run",
                        json={"party": party, "map": map_config}
                    )
                    return response.status_code == 201
                except:
                    return False
        
        # Run 50 concurrent session creations
        print("🚀 Testing concurrent load (50 concurrent requests)...")
        tasks = [create_session_and_run() for _ in range(50)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Count successes
        successes = sum(1 for result in results if result is True)
        success_rate = successes / len(results) * 100
        
        print(f"📊 Load Test Results:")
        print(f"   Total Requests: {len(results)}")
        print(f"   Successful: {successes}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {end_time - start_time:.2f}s")
        print(f"   Avg Response Time: {(end_time - start_time) / len(results) * 1000:.0f}ms")
        
        # System should handle at least 80% success rate under load
        assert success_rate >= 80, f"Success rate {success_rate}% is below 80% threshold"
        print("✅ Concurrent load test passed")

class TestPerformanceValidation:
    """Performance validation and benchmarking."""
    
    @pytest.fixture
    def system_endpoints(self):
        return {
            "router": "http://localhost:59000",
            "backend": "http://localhost:59002"
        }
    
    async def test_response_time_benchmarks(self, system_endpoints):
        """Test response time benchmarks for all endpoints."""
        endpoints = [
            ("Router Health", f"{system_endpoints['router']}/health"),
            ("Router Detailed Health", f"{system_endpoints['router']}/health/detailed"),
            ("Backend Health", f"{system_endpoints['backend']}/health"),
            ("API Root", f"{system_endpoints['router']}/api/"),
        ]
        
        benchmarks = {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for name, url in endpoints:
                response_times = []
                
                # Measure 20 requests
                for _ in range(20):
                    start_time = time.time()
                    response = await client.get(url)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_times.append((end_time - start_time) * 1000)  # Convert to ms
                
                if response_times:
                    benchmarks[name] = {
                        "avg": statistics.mean(response_times),
                        "min": min(response_times),
                        "max": max(response_times),
                        "p95": sorted(response_times)[int(len(response_times) * 0.95)]
                    }
        
        print("📊 Response Time Benchmarks:")
        for endpoint, metrics in benchmarks.items():
            print(f"   {endpoint}:")
            print(f"     Average: {metrics['avg']:.1f}ms")
            print(f"     Min: {metrics['min']:.1f}ms")
            print(f"     Max: {metrics['max']:.1f}ms")
            print(f"     95th Percentile: {metrics['p95']:.1f}ms")
        
        # Validate performance requirements
        for endpoint, metrics in benchmarks.items():
            if "Health" in endpoint:
                assert metrics["avg"] < 100, f"{endpoint} avg response time {metrics['avg']:.1f}ms exceeds 100ms"
                assert metrics["p95"] < 200, f"{endpoint} p95 response time {metrics['p95']:.1f}ms exceeds 200ms"
            else:
                assert metrics["avg"] < 500, f"{endpoint} avg response time {metrics['avg']:.1f}ms exceeds 500ms"
                assert metrics["p95"] < 1000, f"{endpoint} p95 response time {metrics['p95']:.1f}ms exceeds 1000ms"
        
        print("✅ All response time benchmarks passed")
    
    async def test_throughput_validation(self, system_endpoints):
        """Test system throughput capabilities."""
        router_url = system_endpoints["router"]
        
        async def make_health_request():
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = time.time()
                response = await client.get(f"{router_url}/health")
                end_time = time.time()
                return response.status_code == 200, end_time - start_time
        
        # Test throughput over 30 seconds
        print("🚀 Testing system throughput (30 second test)...")
        
        test_duration = 30  # seconds
        start_time = time.time()
        results = []
        
        while time.time() - start_time < test_duration:
            # Send 10 concurrent requests
            tasks = [make_health_request() for _ in range(10)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if not isinstance(result, Exception):
                    results.append(result)
            
            # Brief pause to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for success, _ in results if success)
        total_requests = len(results)
        
        throughput = successful_requests / total_time
        avg_response_time = statistics.mean([rt for _, rt in results]) * 1000
        
        print(f"📊 Throughput Test Results:")
        print(f"   Test Duration: {total_time:.1f}s")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful Requests: {successful_requests}")
        print(f"   Success Rate: {successful_requests / total_requests * 100:.1f}%")
        print(f"   Throughput: {throughput:.1f} requests/second")
        print(f"   Average Response Time: {avg_response_time:.1f}ms")
        
        # Validate throughput requirements
        assert throughput >= 50, f"Throughput {throughput:.1f} req/s is below 50 req/s minimum"
        assert successful_requests / total_requests >= 0.95, "Success rate below 95%"
        
        print("✅ Throughput validation passed")

class TestMonitoringAndObservability:
    """Test monitoring and observability features."""
    
    @pytest.fixture
    def system_endpoints(self):
        return {
            "router": "http://localhost:59000",
            "backend": "http://localhost:59002"
        }
    
    async def test_health_monitoring_comprehensive(self, system_endpoints):
        """Test comprehensive health monitoring."""
        router_url = system_endpoints["router"]
        backend_url = system_endpoints["backend"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test router health endpoints
            endpoints = [
                "/health",
                "/health/detailed", 
                "/health/services/backend"
            ]
            
            for endpoint in endpoints:
                response = await client.get(f"{router_url}{endpoint}")
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "success"
                assert "timestamp" in data["data"]
                
                print(f"✅ Router {endpoint} health check passed")
            
            # Test backend health endpoints
            backend_endpoints = [
                "/health",
                "/health/detailed",
                "/health/database",
                "/health/ready",
                "/health/live"
            ]
            
            for endpoint in backend_endpoints:
                response = await client.get(f"{backend_url}{endpoint}")
                assert response.status_code in [200, 503]  # 503 for degraded state
                
                data = response.json()
                assert "status" in data
                
                print(f"✅ Backend {endpoint} health check passed")
    
    async def test_error_reporting(self, system_endpoints):
        """Test error reporting and tracking."""
        router_url = system_endpoints["router"]
        
        async with httpx.AsyncClient() as client:
            # Test various error scenarios
            error_tests = [
                ("/api/nonexistent", 404),
                ("/api/game/session/invalid/run/invalid", 404),
                ("/api/game/gacha/roll", 400)  # Missing data
            ]
            
            for endpoint, expected_status in error_tests:
                response = await client.get(f"{router_url}{endpoint}")
                assert response.status_code == expected_status
                
                if response.headers.get("content-type", "").startswith("application/json"):
                    data = response.json()
                    # Check for standardized error response
                    if "status" in data:
                        assert data["status"] == "error"
                        assert "message" in data
                
                print(f"✅ Error handling for {endpoint} (status {expected_status}) passed")

class TestDeploymentValidation:
    """Test deployment and scaling scenarios."""
    
    def test_docker_container_health(self):
        """Test Docker container health and status."""
        client = docker.from_env()
        
        required_containers = [
            "autofighter_frontend",
            "autofighter_router", 
            "autofighter_backend",
            "autofighter_database",
            "autofighter_pgadmin"
        ]
        
        for container_name in required_containers:
            try:
                container = client.containers.get(container_name)
                
                assert container.status == "running", f"{container_name} is not running"
                
                # Check health if health check is configured
                if container.attrs.get("State", {}).get("Health"):
                    health_status = container.attrs["State"]["Health"]["Status"]
                    assert health_status in ["healthy", "starting"], f"{container_name} health: {health_status}"
                
                print(f"✅ Container {container_name} is healthy")
                
            except docker.errors.NotFound:
                pytest.fail(f"Required container {container_name} not found")
    
    def test_docker_network_connectivity(self):
        """Test Docker network connectivity between services."""
        client = docker.from_env()
        
        # Get autofighter network
        networks = client.networks.list(names=["autofighter_autofighter_network"])
        assert len(networks) > 0, "AutoFighter network not found"
        
        network = networks[0]
        containers = network.attrs["Containers"]
        
        required_services = ["frontend", "router", "backend", "database"]
        found_services = []
        
        for container_id, container_info in containers.items():
            container = client.containers.get(container_id)
            service_name = container.name.replace("autofighter_", "")
            if any(service in service_name for service in required_services):
                found_services.append(service_name)
        
        print(f"📡 Found services on network: {found_services}")
        
        # Verify all required services are connected
        for service in required_services:
            assert any(service in found_service for found_service in found_services), f"Service {service} not found on network"
        
        print("✅ All services are properly networked")
    
    async def test_service_dependencies(self):
        """Test service dependency chain."""
        # Test dependency chain: Frontend -> Router -> Backend -> Database
        
        services = [
            ("Database", "postgresql://autofighter:password@localhost:5432/autofighter"),
            ("Backend", "http://localhost:59002/health"),
            ("Router", "http://localhost:59000/health"),
            ("Frontend", "http://localhost:59001")
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for service_name, endpoint in services:
                if service_name == "Database":
                    # Test database connectivity
                    try:
                        conn = psycopg2.connect(
                            host="localhost",
                            port=5432,
                            database="autofighter",
                            user="autofighter",
                            password="password",
                            connect_timeout=10
                        )
                        conn.close()
                        print(f"✅ {service_name} dependency available")
                    except Exception as e:
                        pytest.fail(f"{service_name} dependency failed: {e}")
                else:
                    # Test HTTP services
                    try:
                        response = await client.get(endpoint)
                        assert response.status_code == 200
                        print(f"✅ {service_name} dependency available")
                    except Exception as e:
                        pytest.fail(f"{service_name} dependency failed: {e}")
        
        print("✅ All service dependencies validated")
```

### Step 2: System Monitoring Setup

**File**: `monitoring/health-monitor.py`
```python
#!/usr/bin/env python3
"""
Continuous health monitoring for AutoFighter system
"""

import asyncio
import httpx
import psycopg2
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import smtplib
from email.mime.text import MimeText

class HealthMonitor:
    """Continuous health monitoring system."""
    
    def __init__(self, config_file="monitoring/config.json"):
        with open(config_file) as f:
            self.config = json.load(f)
        
        self.setup_logging()
        self.health_history = []
        self.alert_cooldowns = {}
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitoring/health.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def check_service_health(self, service_name: str, endpoint: str) -> Dict[str, Any]:
        """Check health of a single service."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = time.time()
                response = await client.get(endpoint)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    return {
                        "service": service_name,
                        "status": "healthy",
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "service": service_name,
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "service": service_name,
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            start_time = time.time()
            conn = psycopg2.connect(
                host=self.config["database"]["host"],
                port=self.config["database"]["port"],
                database=self.config["database"]["database"],
                user=self.config["database"]["user"],
                password=self.config["database"]["password"],
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            response_time = time.time() - start_time
            
            return {
                "service": "database",
                "status": "healthy",
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "service": "database",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_all_services(self) -> List[Dict[str, Any]]:
        """Check health of all services."""
        results = []
        
        # Check HTTP services
        for service in self.config["services"]:
            result = await self.check_service_health(service["name"], service["endpoint"])
            results.append(result)
        
        # Check database
        db_result = self.check_database_health()
        results.append(db_result)
        
        return results
    
    def send_alert(self, service: str, issue: str):
        """Send alert notification."""
        # Check cooldown
        cooldown_key = f"{service}_{issue}"
        now = datetime.now()
        
        if cooldown_key in self.alert_cooldowns:
            if now - self.alert_cooldowns[cooldown_key] < timedelta(minutes=15):
                return  # Skip alert due to cooldown
        
        self.alert_cooldowns[cooldown_key] = now
        
        # Send email alert
        if self.config.get("alerts", {}).get("email", {}).get("enabled"):
            self.send_email_alert(service, issue)
        
        self.logger.error(f"ALERT: {service} - {issue}")
    
    def send_email_alert(self, service: str, issue: str):
        """Send email alert."""
        email_config = self.config["alerts"]["email"]
        
        subject = f"AutoFighter Alert: {service} Issue"
        body = f"""
AutoFighter Health Monitor Alert

Service: {service}
Issue: {issue}
Time: {datetime.now().isoformat()}

Please check the system status immediately.
        """
        
        msg = MimeText(body)
        msg['Subject'] = subject
        msg['From'] = email_config["from"]
        msg['To'] = email_config["to"]
        
        try:
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def analyze_health_trends(self) -> Dict[str, Any]:
        """Analyze health trends over time."""
        if len(self.health_history) < 10:
            return {"status": "insufficient_data"}
        
        # Get last 24 hours of data
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_data = [
            record for record in self.health_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]
        
        if not recent_data:
            return {"status": "no_recent_data"}
        
        # Calculate service availability
        service_stats = {}
        for record in recent_data:
            service = record["service"]
            if service not in service_stats:
                service_stats[service] = {"total": 0, "healthy": 0, "response_times": []}
            
            service_stats[service]["total"] += 1
            if record["status"] == "healthy":
                service_stats[service]["healthy"] += 1
                if "response_time" in record:
                    service_stats[service]["response_times"].append(record["response_time"])
        
        # Calculate availability percentages
        availability = {}
        for service, stats in service_stats.items():
            availability[service] = {
                "uptime_percentage": (stats["healthy"] / stats["total"]) * 100,
                "total_checks": stats["total"],
                "avg_response_time": sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0
            }
        
        return {
            "status": "analyzed",
            "period": "24_hours",
            "availability": availability,
            "total_records": len(recent_data)
        }
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        self.logger.info("Starting AutoFighter health monitoring...")
        
        while True:
            try:
                # Check all services
                health_results = await self.check_all_services()
                
                # Store results
                for result in health_results:
                    self.health_history.append(result)
                
                # Keep only last 1000 records
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]
                
                # Check for issues and send alerts
                for result in health_results:
                    if result["status"] != "healthy":
                        self.send_alert(result["service"], result.get("error", "Service unhealthy"))
                    elif result.get("response_time", 0) > 5.0:  # Slow response
                        self.send_alert(result["service"], f"Slow response time: {result['response_time']:.2f}s")
                
                # Log status
                healthy_services = sum(1 for r in health_results if r["status"] == "healthy")
                self.logger.info(f"Health check complete: {healthy_services}/{len(health_results)} services healthy")
                
                # Periodic trend analysis
                if len(self.health_history) % 60 == 0:  # Every 60 checks
                    trends = self.analyze_health_trends()
                    if trends["status"] == "analyzed":
                        self.logger.info(f"Trend analysis: {trends}")
                
                # Wait before next check
                await asyncio.sleep(self.config["check_interval"])
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)  # Wait before retrying

if __name__ == "__main__":
    monitor = HealthMonitor()
    asyncio.run(monitor.monitor_loop())
```

**File**: `monitoring/config.json`
```json
{
    "check_interval": 60,
    "services": [
        {
            "name": "frontend",
            "endpoint": "http://localhost:59001"
        },
        {
            "name": "router",
            "endpoint": "http://localhost:59000/health"
        },
        {
            "name": "backend", 
            "endpoint": "http://localhost:59002/health"
        },
        {
            "name": "pgadmin",
            "endpoint": "http://localhost:38085"
        }
    ],
    "database": {
        "host": "localhost",
        "port": 5432,
        "database": "autofighter",
        "user": "autofighter",
        "password": "password"
    },
    "alerts": {
        "email": {
            "enabled": false,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "your-email@gmail.com",
            "password": "your-app-password",
            "from": "autofighter-monitor@yourdomain.com",
            "to": "admin@yourdomain.com"
        }
    }
}
```

### Step 3: System Documentation

**File**: `docs/SYSTEM_VALIDATION.md`
```markdown
# AutoFighter System Validation Guide

## Overview

This document provides comprehensive guidance for validating the AutoFighter system deployment, performance, and reliability.

## System Architecture Validation

### Service Communication Flow
```
Frontend (59001) → Router (59000) → Backend (59002) → Database (5432)
                                                    ↓
                                                pgAdmin (38085)
```

### Validation Checklist

#### ✅ Infrastructure Validation
- [ ] All Docker containers are running
- [ ] Custom network connectivity established
- [ ] Volume mounts working for development
- [ ] Health checks passing for all services
- [ ] Port mappings configured correctly

#### ✅ Service Integration Validation
- [ ] Frontend can reach router service
- [ ] Router forwards requests to backend correctly
- [ ] Backend can connect to PostgreSQL database
- [ ] pgAdmin can access database
- [ ] All APIs return standardized responses

#### ✅ Data Flow Validation
- [ ] Game sessions can be created
- [ ] Player data persists correctly
- [ ] Gacha system generates and stores items
- [ ] Upgrade points are tracked accurately
- [ ] All data survives service restarts

#### ✅ Performance Validation
- [ ] Health checks respond within 100ms
- [ ] API requests complete within 500ms
- [ ] System handles 50+ concurrent requests
- [ ] Database queries execute efficiently
- [ ] No memory leaks or resource issues

#### ✅ Reliability Validation
- [ ] System recovers from service restarts
- [ ] Error handling works correctly
- [ ] Data integrity maintained under load
- [ ] Monitoring and alerting functional
- [ ] Graceful degradation during failures

## Testing Procedures

### 1. Manual Validation Tests

#### Frontend Access Test
```bash
curl -I http://localhost:59001
# Expected: HTTP/1.1 200 OK
```

#### Router Health Test
```bash
curl http://localhost:59000/health
# Expected: {"status": "success", "data": {"status": "healthy"}}
```

#### Backend Health Test
```bash
curl http://localhost:59002/health
# Expected: {"status": "success", "data": {"status": "healthy"}}
```

#### Database Connection Test
```bash
docker-compose exec database psql -U autofighter -d autofighter -c '\l'
# Expected: List of databases including 'autofighter'
```

#### pgAdmin Access Test
```bash
curl -I http://localhost:38085
# Expected: HTTP/1.1 200 OK or 302 (redirect to login)
```

### 2. Automated System Tests

#### Run Complete System Validation
```bash
cd tests/system
python -m pytest test_system_validation.py -v
```

#### Run Performance Benchmarks
```bash
python -m pytest test_system_validation.py::TestPerformanceValidation -v
```

#### Run Resilience Tests
```bash
python -m pytest test_system_validation.py::TestSystemValidation::test_system_resilience -v
```

### 3. Load Testing

#### Concurrent Session Creation
```bash
python -m pytest test_system_validation.py::TestSystemValidation::test_concurrent_load_handling -v
```

#### Throughput Testing
```bash
python -m pytest test_system_validation.py::TestPerformanceValidation::test_throughput_validation -v
```

### 4. Monitoring Setup

#### Start Health Monitor
```bash
cd monitoring
python health-monitor.py
```

#### View Health Logs
```bash
tail -f monitoring/health.log
```

## Performance Benchmarks

### Response Time Targets
- **Health Endpoints**: < 100ms average, < 200ms 95th percentile
- **API Endpoints**: < 500ms average, < 1000ms 95th percentile
- **Database Queries**: < 50ms for simple queries

### Throughput Targets
- **Health Checks**: > 100 requests/second
- **API Requests**: > 50 requests/second
- **Concurrent Sessions**: > 20 simultaneous sessions

### Resource Usage Targets
- **CPU Usage**: < 70% average per service
- **Memory Usage**: < 80% of allocated memory
- **Database Connections**: < 50% of max connections

## Troubleshooting Guide

### Common Issues

#### Services Not Starting
1. Check Docker container status: `docker-compose ps`
2. View service logs: `docker-compose logs [service-name]`
3. Verify port availability: `netstat -ln | grep [port]`
4. Check Docker network: `docker network ls`

#### Database Connection Issues
1. Verify PostgreSQL is running: `docker-compose logs database`
2. Test connection: `docker-compose exec database pg_isready`
3. Check credentials in environment variables
4. Verify network connectivity between services

#### High Response Times
1. Check system resource usage: `docker stats`
2. Monitor database performance: Check pgAdmin for slow queries
3. Review application logs for bottlenecks
4. Consider scaling if load is high

#### Health Check Failures
1. Verify service is actually running
2. Check if health endpoint is accessible
3. Review service logs for errors
4. Test manual requests to health endpoints

### Recovery Procedures

#### Service Recovery
```bash
# Restart specific service
docker-compose restart [service-name]

# Rebuild and restart service
docker-compose up -d --build [service-name]

# Full system restart
docker-compose down && docker-compose up -d
```

#### Database Recovery
```bash
# Restart database
docker-compose restart database

# Backup database
docker-compose exec database pg_dump -U autofighter autofighter > backup.sql

# Restore database
docker-compose exec -T database psql -U autofighter autofighter < backup.sql
```

## Deployment Validation

### Pre-Deployment Checklist
- [ ] All tests passing in staging environment
- [ ] Performance benchmarks meet requirements
- [ ] Security scan completed
- [ ] Backup procedures verified
- [ ] Monitoring configured
- [ ] Rollback plan prepared

### Post-Deployment Validation
- [ ] All services healthy in production
- [ ] End-to-end user flows working
- [ ] Performance within acceptable ranges
- [ ] Monitoring alerts configured
- [ ] Log aggregation working
- [ ] Backup verification completed

## Monitoring and Alerting

### Key Metrics to Monitor
- Service availability and response times
- Database connection pool usage
- API error rates and response codes
- System resource utilization
- User session success rates

### Alert Thresholds
- Service downtime > 1 minute
- Response time > 2x normal average
- Error rate > 5%
- CPU usage > 80% for 5+ minutes
- Memory usage > 90%
- Database connection failures

### Monitoring Tools
- Built-in health endpoints
- Custom health monitor script
- Docker container monitoring
- PostgreSQL performance monitoring via pgAdmin
- Log aggregation and analysis

## Conclusion

Regular system validation ensures the AutoFighter platform remains reliable, performant, and available for users. Follow this guide to maintain system health and quickly identify and resolve issues.
```

### Step 4: System Test Runner

**File**: `scripts/run-system-validation.sh`
```bash
#!/bin/bash
set -e

echo "=== AutoFighter Complete System Validation ==="
echo ""

# Check if services are running
echo "🔍 Checking if services are running..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Services are not running. Starting services..."
    ./scripts/compose-dev.sh up
    echo "⏳ Waiting for services to stabilize..."
    sleep 60
fi

echo "✅ Services are running"
echo ""

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio httpx psycopg2-binary docker requests

# Run system validation tests
echo ""
echo "🧪 Running Complete System Validation..."
echo ""

# Set test environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run validation test suites
echo ">>> System Validation Tests"
python -m pytest tests/system/test_system_validation.py::TestSystemValidation -v

echo ""
echo ">>> Performance Validation Tests"  
python -m pytest tests/system/test_system_validation.py::TestPerformanceValidation -v

echo ""
echo ">>> Monitoring and Observability Tests"
python -m pytest tests/system/test_system_validation.py::TestMonitoringAndObservability -v

echo ""
echo ">>> Deployment Validation Tests"
python -m pytest tests/system/test_system_validation.py::TestDeploymentValidation -v

echo ""
echo "🎉 Complete System Validation Passed!"

# Generate system report
echo ""
echo "📊 Generating System Health Report..."

# Create report directory
mkdir -p reports

# Generate health report
cat > reports/system-health-report.md << 'EOF'
# AutoFighter System Health Report

Generated: $(date)

## Service Status
EOF

# Check each service and add to report
for service in frontend router backend database pgadmin; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "- ✅ $service: Running" >> reports/system-health-report.md
    else
        echo "- ❌ $service: Not Running" >> reports/system-health-report.md
    fi
done

echo "" >> reports/system-health-report.md
echo "## Performance Metrics" >> reports/system-health-report.md
echo "- Tests completed at: $(date)" >> reports/system-health-report.md
echo "- All performance benchmarks: PASSED" >> reports/system-health-report.md

echo ""
echo "📄 System health report generated: reports/system-health-report.md"

# Start health monitoring if requested
read -p "Start continuous health monitoring? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Starting health monitoring..."
    cd monitoring
    python health-monitor.py &
    echo "Health monitoring started in background (PID: $!)"
    echo "View logs: tail -f monitoring/health.log"
fi

echo ""
echo "🎊 System validation complete! System is ready for production use."
```

## Validation Criteria

### Success Criteria
1. **Complete System Function**: All user workflows work end-to-end
2. **Performance Standards**: All response time and throughput benchmarks met
3. **Reliability Standards**: System handles failures and recovers gracefully
4. **Monitoring Coverage**: Comprehensive health monitoring and alerting working
5. **Documentation Complete**: All system documentation and runbooks available

### Validation Commands
```bash
# Run complete system validation
chmod +x scripts/run-system-validation.sh
./scripts/run-system-validation.sh

# Run specific validation categories
python -m pytest tests/system/test_system_validation.py::TestSystemValidation -v
python -m pytest tests/system/test_system_validation.py::TestPerformanceValidation -v

# Start health monitoring
cd monitoring
python health-monitor.py

# Generate system report
./scripts/compose-dev.sh status
./scripts/health-check.sh
```

### Expected Results
- All system validation tests pass
- Performance benchmarks meet requirements
- System handles load and failure scenarios
- Health monitoring detects and reports issues
- Complete documentation available
- System ready for production deployment

## Notes

- System validation requires all services to be running
- Performance tests establish baseline metrics for monitoring
- Health monitoring provides continuous system oversight
- Documentation serves as operational runbook
- Validation should be run before any production deployment