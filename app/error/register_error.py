from fastapi import status, FastAPI
from app.error.custom_exception import (
    RateLimit,
    UserNotVerified,
    UsernameExist,
    UserMailExist,
    UserUnauthenticated,
    InvalidToken,
    UserNotAuthenticated,
    UserNotFound,
    create_exception_handler,
    create_global_handler,
)
from app.error.validation_exception import ValidationError, SanitizationError
from app.core.recovery import CircuitOpenError


def register_exception(app: FastAPI):
    """Register all custom exception handlers for the application."""

    # User-related exceptions
    app.add_exception_handler(
        UsernameExist,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Username already exists",
                "error_code": "username_exists"
            }
        )
    )

    app.add_exception_handler(
        UserMailExist,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Email already exists",
                "error_code": "email_exists"
            }
        )
    )

    app.add_exception_handler(
        UserUnauthenticated,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "Invalid authentication credentials",
                "error_code": "user_unauthenticated"
            }
        )
    )

    app.add_exception_handler(
        UserNotVerified,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN
        )
    )

    app.add_exception_handler(
        InvalidToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "Invalid or expired token",
                "error_code": "invalid_token"
            }
        )
    )

    app.add_exception_handler(
        UserNotAuthenticated,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "Authentication required",
                "error_code": "not_authenticated"
            }
        )
    )

    app.add_exception_handler(
        UserNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "User not found",
                "error_code": "user_not_found"
            }
        )
    )

    # Rate limiting exception
    app.add_exception_handler(
        RateLimit,
        create_exception_handler(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    )

    # Global exception handler for unexpected errors
    app.add_exception_handler(
        Exception,
        create_global_handler(
            status_code=500,
            initial_detail={
                "message": "Internal Server Error",
            }
        )
    )

    # Circuit breaker exception
    app.add_exception_handler(
        CircuitOpenError,
        create_exception_handler(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            initial_detail={
                "message": "Service temporarily unavailable due to high failure rate",
                "error_code": "service_unavailable"
            }
        )
    )

    # Validation exceptions
    app.add_exception_handler(
        ValidationError,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Input validation failed",
                "error_code": "validation_error"
            }
        )
    )

    app.add_exception_handler(
        SanitizationError,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Input contains invalid or dangerous content",
                "error_code": "sanitization_error"
            }
        )
    )
