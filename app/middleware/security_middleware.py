"""Security middleware: security headers enforcement and request body sanitization."""

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.core.logger import logger
from app.core.security.validation import safe_str

# Default security headers
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
}


def register_security_middleware(app: FastAPI):
    """Register middleware that adds security headers to every response."""

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response: Response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response