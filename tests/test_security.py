"""Tests for security middleware and validation integration."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "default-src" in response.headers.get("Content-Security-Policy", "")


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_liveness_probe(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_valid_response(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data
        # With SQLite test DB, database health should be healthy
        db_checks = [c for c in data["checks"] if c["service"] == "database"]
        if db_checks:
            assert db_checks[0]["healthy"] is True