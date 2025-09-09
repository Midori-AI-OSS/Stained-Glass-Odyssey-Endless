"""
Test the performance monitoring endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(app_with_db):
    """Test the health check endpoint."""
    app, _ = app_with_db

    async with app.test_client() as client:
        response = await client.get("/api/performance/health")
        assert response.status_code == 200

        data = await response.get_json()
        assert "status" in data
        assert "timestamp" in data
        assert "ping_ms" in data
        assert data["status"] in ["ok", "degraded", "error"]


@pytest.mark.asyncio
async def test_metrics_endpoint(app_with_db):
    """Test the event bus metrics endpoint."""
    app, _ = app_with_db

    async with app.test_client() as client:
        response = await client.get("/api/performance/metrics")
        assert response.status_code == 200

        data = await response.get_json()
        assert "health" in data
        assert "metrics" in data
        assert "summary" in data

        # Health should have status and timestamp
        assert "status" in data["health"]
        assert "timestamp" in data["health"]

        # Summary should have counts
        assert "total_events" in data["summary"]
        assert "total_errors" in data["summary"]


@pytest.mark.asyncio
async def test_clear_metrics_endpoint(app_with_db):
    """Test the clear metrics endpoint."""
    app, _ = app_with_db

    async with app.test_client() as client:
        response = await client.post("/api/performance/metrics/clear")
        assert response.status_code == 200

        data = await response.get_json()
        assert data["status"] == "ok"
        assert "message" in data
