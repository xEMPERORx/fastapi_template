"""
Automated health-check logic.

Provides status checks for:
- Database connectivity
- Redis connectivity
- Elasticsearch connectivity
- Overall application health
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

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


async def check_db(db_session_factory) -> HealthStatus:
    """Ping the database with a lightweight query."""
    start = time.monotonic()
    try:
        async with db_session_factory() as session:
            await session.execute("SELECT 1")
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


async def check_elasticsearch(es_client) -> HealthStatus:
    """Ping Elasticsearch."""
    start = time.monotonic()
    try:
        healthy = await es_client.ping()
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            healthy=bool(healthy),
            service="elasticsearch",
            latency_ms=latency,
            detail="OK" if healthy else "ping returned False",
        )
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        logger.exception("Elasticsearch health check failed")
        return HealthStatus(
            healthy=False, service="elasticsearch", latency_ms=latency, detail=str(exc)
        )


async def run_all_checks(
    db_session_factory,
    redis_client=None,
    es_client=None,
) -> HealthReport:
    """Run all registered health checks and aggregate the result."""
    checks: list[HealthStatus] = []

    if db_session_factory:
        checks.append(await check_db(db_session_factory))

    if redis_client:
        checks.append(await check_redis(redis_client))

    if es_client:
        checks.append(await check_elasticsearch(es_client))

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