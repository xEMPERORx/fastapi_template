"""Exceptions raised by the auth/user domain (registration, login, tokens,
mail verification, password reset — see `app.services.auth`/`app.services.verify`).
"""

from typing import Any

from app.error.base import AppException


class UserException(AppException):
    pass


class UsernameExist(UserException):
    def __init__(self, user_name: Any = "unknown"):
        super().__init__(
            message=f"User with this username: {user_name} already exists",
            error_code="user_exists"
        )

class UserMailExist(UserException):
    def __init__(self, user_email: Any = "unknown"):
        super().__init__(
            message=f"User with this email:{user_email} already exists",
            error_code="email_exists"
        )

class UserUnauthenticated(UserException):
    def __init__(self):
        super().__init__(
            message=f"Invalid username or password",
            error_code="user_unauthenticated"
        )

class UserNotVerified(UserException):
    def __init__(self):
        super().__init__(
            message=f"User Not Verified",
            error_code="user_not_verified"
        )

class InvalidToken(UserException):
    def __init__(self):
        super().__init__(
            message="Invalid or expired authentication token",
            error_code="invalid_token"
        )

class UserNotAuthenticated(UserException):
    def __init__(self):
        super().__init__(
            message="Authentication required. Please login to access this resource",
            error_code="not_authenticated"
        )

class UserNotFound(UserException):
    def __init__(self, username: Any = "unknown"):
        super().__init__(
            message=f"User {username} not found",
            error_code="user_not_found"
        )

class UserDeactivated(UserException):
    def __init__(self):
        super().__init__(
            message="This account has been deactivated",
            error_code="user_deactivated"
        )

class TenantInactive(UserException):
    def __init__(self):
        super().__init__(
            message="This organization has been deactivated",
            error_code="tenant_inactive"
        )

class StaleToken(UserException):
    def __init__(self):
        super().__init__(
            message="Your permissions have changed; please refresh your session",
            error_code="stale_token"
        )
