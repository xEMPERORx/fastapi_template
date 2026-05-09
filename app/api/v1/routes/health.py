"""Health check API endpoints."""

from fastapi import APIRouter, Depends

from app.core.dependency_factory import get_db
from app.core.esclient import es_client as _es_client
from app.core.health import HealthReport, run_all_checks
from app.core.logger import log_function
from app.database.db import get_db as get_db_session

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=dict)
@log_function
async def health_check():
    """Return aggregated health status of all backend services."""
    report: HealthReport = await run_all_checks(
        db_session_factory=get_db_session,
        es_client=_es_client,
    )
    return report.to_dict()


@router.get("/health/live")
async def liveness():
    """Kubernetes-style liveness probe: always 200 if app is running."""
    return {"status": "alive"}


@router.get("/health/ready")
@log_function
async def readiness():
    """Kubernetes-style readiness probe: 200 only if critical services are healthy."""
    report: HealthReport = await run_all_checks(
        db_session_factory=get_db_session,
        es_client=_es_client,
    )
    if report.status == "unhealthy":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=report.to_dict())
    return report.to_dict()