from fastapi import FastAPI, Request

from app.core.logger import log_error, logger
from app.core.fixed_window_ratelimit import FixedWindowLimiter
from app.error.custom_exception import RateLimit

limiter = FixedWindowLimiter(requests=10, window_seconds=60)


def register_ratelimit_middleware(app: FastAPI):
    """Register rate limiting middleware."""

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        logger.info("Rate limit check for %s", client_ip)

        try:
            if not limiter.is_allowed(client_ip):
                raise RateLimit(
                    message="Too many requests. Please slow down.",
                    headers={
                        "X-RateLimit-Limit": str(limiter.requests),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(limiter.window)
                    }
                )

            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limiter.requests)
            response.headers["X-RateLimit-Remaining"] = str(limiter.get_remaining(client_ip))

            return response

        except Exception as exc:
            log_error(
                error_type=type(exc).__name__,
                message=str(exc),
                error_location=f"Rate limit middleware: {client_ip}",
                exc_info=True,
                layer="middleware",
            )
            handler = app.exception_handlers.get(RateLimit)
            return await handler(request, exc)
