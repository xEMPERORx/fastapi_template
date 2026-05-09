"""
Data validation and integrity utilities.

Provides:
- Data integrity checks for models
- Field-level sanitization
- Schema validation helpers
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ValidationError


# ---------------------------------------------------------------------------
# Data integrity helpers
# ---------------------------------------------------------------------------

# Common dangerous characters for file paths / names
_PATH_TRAVERSAL_RE = re.compile(r"\.\./|\.\.\\|%2e%2e%2f|%2e%2e/")


def safe_filename(value: str, max_len: int = 255) -> str:
    """Strip path-traversal and dangerous chars, return safe filename."""
    value = _PATH_TRAVERSAL_RE.sub("", value)
    # Keep only word chars, dots, dashes, underscores
    value = re.sub(r"[^\w.\-]", "_", value)
    return value[:max_len].strip("._")


def validate_model_fields(data: dict[str, Any], model_cls: type[BaseModel]) -> BaseModel:
    """Validate and coerce raw dict data against a Pydantic model."""
    return model_cls.model_validate(data)


def validate_required_fields(
    data: dict[str, Any],
    required: list[str],
    field_label: str = "field",
) -> None:
    """Raise ValueError if any required key is missing or empty."""
    for key in required:
        if key not in data or data[key] is None or (isinstance(data[key], str) and not data[key].strip()):
            raise ValueError(f"Missing required {field_label}: '{key}'")


def sanitize_dict(data: dict[str, Any], max_str_len: int = 10_000) -> dict[str, Any]:
    """Recursively trim overly-long strings in a dict."""
    result: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = v[:max_str_len]
        elif isinstance(v, dict):
            result[k] = sanitize_dict(v, max_str_len)
        elif isinstance(v, list):
            result[k] = [
                sanitize_dict(item, max_str_len) if isinstance(item, dict)
                else item[:max_str_len] if isinstance(item, str)
                else item
                for item in v
            ]
        else:
            result[k] = v
    return result