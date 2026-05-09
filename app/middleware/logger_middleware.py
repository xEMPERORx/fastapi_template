import time
import uuid

from fastapi import FastAPI, Request

from app.core.logger import (
    log_error,
    log_request_end,
    log_request_start,
    set_request_id,
)

def register_logger_middleware(app: FastAPI):
    """Register request/response logging middleware."""

    @app.middleware("http")
    async def dispatch(request: Request, call_next):
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        request.state.request_id = request_id

        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = request.url.path
        query_params = dict(request.query_params) if request.query_params else None

        log_request_start(method, url, client_ip, query_params)

        start = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            response.headers["X-Request-ID"] = request_id
            log_request_end(response.status_code, duration_ms)
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            log_error(
                error_type=type(exc).__name__,
                message=str(exc),
                error_location=f"Middleware: {method} {url}",
                exc_info=True,
                layer="middleware",
            )
            log_request_end(500, duration_ms)
            handler = app.exception_handlers.get(Exception)
            response = await handler(request, exc)
            response.headers["X-Request-ID"] = request_id
            return response
