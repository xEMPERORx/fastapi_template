"""
Automated health-check logic.

Provides status checks for:
- Database connectivity
- Redis connectivity
- Overall application health
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger


@dataclass
class HealthStatus:
    healthy: bool
    service: str
    latency_ms: float = 0.0
    detail: str = ""


@dataclass
class HealthReport:
    status: str  # "healthy" | "degraded" | "unhealthy"
    checks: list[HealthStatus] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": [
                {
                    "service": c.service,
                    "healthy": c.healthy,
                    "latency_ms": round(c.latency_ms, 3),
                    "detail": c.detail,
                }
                for c in self.checks
            ],
            "timestamp": self.timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


async def check_db(db: AsyncSession) -> HealthStatus:
    """Ping the database with a lightweight query using an already-open session.

    Takes a session resolved through FastAPI's normal `Depends(get_db)` (see
    app/api/v1/routes/health.py) rather than a raw session-factory function —
    that way it shares the same connection-acquisition path (and, in tests,
    the same dependency override) as every other route, instead of driving
    a second, independently-constructed engine by hand.
    """
    start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(healthy=True, service="database", latency_ms=latency, detail="OK")
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        logger.exception("DB health check failed")
        return HealthStatus(healthy=False, service="database", latency_ms=latency, detail=str(exc))


async def check_redis(redis_client) -> HealthStatus:
    """Ping Redis."""
    start = time.monotonic()
    try:
        await redis_client.ping()
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(healthy=True, service="redis", latency_ms=latency, detail="OK")
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        logger.exception("Redis health check failed")
        return HealthStatus(healthy=False, service="redis", latency_ms=latency, detail=str(exc))


async def run_all_checks(
    db: AsyncSession | None = None,
    redis_client=None,
) -> HealthReport:
    """Run all registered health checks and aggregate the result."""
    checks: list[HealthStatus] = []

    if db is not None:
        checks.append(await check_db(db))

    if redis_client:
        checks.append(await check_redis(redis_client))

    if not checks:
        return HealthReport(status="healthy", checks=[], timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    all_healthy = all(c.healthy for c in checks)
    any_healthy = any(c.healthy for c in checks)

    if all_healthy:
        status = "healthy"
    elif any_healthy:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthReport(status=status, checks=checks, timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"))