"""
Advanced input validation and sanitization utilities.

Provides:
- Pydantic field validators for common types (email, phone, URL, etc.)
- Sanitization functions to strip XSS and injection payloads
- Reusable validation dependencies for FastAPI routes
"""

import re
import html
from typing import Annotated, Any
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Query, status
from pydantic import AfterValidator, BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

_SQL_KEYWORDS_RE = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|UNION|"
    r"OR\s+\d+\s*=\s*\d+|'\s*OR\s*')\b",
    re.IGNORECASE,
)

_XSS_PATTERNS = [
    re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=\s*[\"'].*?[\"']", re.IGNORECASE),
    re.compile(r"<iframe[^>]*>", re.IGNORECASE),
    re.compile(r"&#x?[0-9a-f]+;", re.IGNORECASE),
]


def strip_html(value: str) -> str:
    """HTML-encode a string so tags are rendered inert."""
    return html.escape(value, quote=True)


def sanitize_text(value: str) -> str:
    """Strip common XSS and SQL-injection signatures from a plain-text field."""
    for pattern in _XSS_PATTERNS:
        value = pattern.sub("", value)
    value = _SQL_KEYWORDS_RE.sub("", value)
    return value.strip()


def safe_str(value: Any) -> str:
    """Convert any value to a safe string, stripping HTML and injection markers."""
    return sanitize_text(strip_html(str(value)))


# ---------------------------------------------------------------------------
# Pydantic reusable validators (can be used via AfterValidator or field_validator)
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")
STRONG_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?])"
    r".{8,128}$"
)


def validate_email(value: str) -> str:
    if not EMAIL_RE.match(value):
        raise ValueError("Invalid email format")
    return value.lower().strip()


def validate_phone(value: str) -> str:
    if not PHONE_RE.match(value):
        raise ValueError("Invalid phone number format")
    return value.strip()


def validate_strong_password(value: str) -> str:
    if not STRONG_PASSWORD_RE.match(value):
        raise ValueError(
            "Password must be 8-128 chars with uppercase, lowercase, digit, and special character"
        )
    return value


def validate_no_sql_injection(value: str) -> str:
    if _SQL_KEYWORDS_RE.search(value):
        raise ValueError("Value contains potentially dangerous SQL patterns")
    return value.strip()


def validate_length(min_len: int = 1, max_len: int = 1000):
    def _check(value: str) -> str:
        if not (min_len <= len(value) <= max_len):
            raise ValueError(f"Length must be between {min_len} and {max_len}")
        return value
    return _check


# ---------------------------------------------------------------------------
# Composite annotated types (drop-in in schema classes)
# ---------------------------------------------------------------------------

SafeStr = Annotated[str, AfterValidator(sanitize_text)]
SafeEmail = Annotated[str, AfterValidator(validate_email), AfterValidator(sanitize_text)]
StrongPassword = Annotated[str, AfterValidator(validate_strong_password)]


# ---------------------------------------------------------------------------
# Reusable FastAPI dependencies
# ---------------------------------------------------------------------------

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=20, ge=1, le=100)


class StrictPaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("page", "page_size", mode="before")
    @classmethod
    def coerce_ints(cls, v: Any) -> int:
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError("Must be a valid integer")


async def pagination_dependency(
    page: int = Query(default=1, ge=1, le=10_000),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)