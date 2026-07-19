"""Base exception type and the generic FastAPI exception-handler factories
that every domain-specific exception module in this package is registered
through (see `app.error.register`).
"""

import logging
from typing import Any, Callable, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.error.ratelimit import RateLimit

logger = logging.getLogger("app")


class AppException(Exception):
    """Base class for all custom application errors."""

    def __init__(self, message: str, error_code: str = "internal_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


def create_exception_handler(
    status_code: int,
    initial_detail: Optional[Dict[str, Any]] = None
) -> Callable[[Request, Exception], JSONResponse]:
    """
    A factory that creates handlers for custom exceptions.
    """
    async def handler(req: Request, exc: Exception) -> JSONResponse:
        message = getattr(exc, "message", str(exc))
        error_type = getattr(exc, "error_code", type(exc).__name__)
        log_level = logging.WARNING
        logger.log(log_level, f"Error at {req.method} {req.url.path} | {error_type}: {str(exc)}")

        if isinstance(exc, RateLimit):
            headers = exc.headers
            return JSONResponse(
                status_code=status_code,
                content={
                    "status": "error",
                    "message": message,
                    "error_code": error_type,
                    "headers": headers,
                },
            )


        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "message": message,
                "error_code": error_type,
                "technical_details": str(exc) if status_code == 500 else None,
            },
        )



    return handler

def create_global_handler(status_code: int, initial_detail: dict) -> Callable:
    """Factory to create the global handler exception"""
    async def custom_handler(req: Request, exc: Exception):

        error_type = type(exc).__name__
        error_msg = str(exc) if str(exc) else f"Internal {error_type} occurred"

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "message": initial_detail.get("message", "Internal Server Error"),
                "error_code": error_type,
                "technical_details": error_msg
            }
        )
    return custom_handler
