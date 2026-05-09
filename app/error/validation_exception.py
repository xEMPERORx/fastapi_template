"""
Custom exceptions for input validation errors.
"""

from app.error.custom_exception import AppException


class ValidationError(AppException):
    """Base class for all validation-related errors."""
    def __init__(self, message: str, field: str = "input"):
        super().__init__(message, "validation_error")
        self.field = field


class SanitizationError(AppException):
    """Raised when input sanitization fails."""
    def __init__(self, message: str = "Input contains invalid characters", field: str = "input"):
        super().__init__(message, "sanitization_error")
        self.field = field