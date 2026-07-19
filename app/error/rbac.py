"""Exceptions raised by the RBAC domain (roles, permissions, grant delegation
— see `app.services.rbac`/`app.services.users`).
"""

from typing import Any

from app.error.base import AppException


class RBACException(AppException):
    pass


class RoleNotFound(RBACException):
    def __init__(self, role_id: Any = "unknown"):
        super().__init__(
            message=f"Role {role_id} not found",
            error_code="role_not_found"
        )


class RoleExists(RBACException):
    def __init__(self, name: Any = "unknown"):
        super().__init__(
            message=f"Role '{name}' already exists",
            error_code="role_exists"
        )


class PermissionNotFound(RBACException):
    def __init__(self, permission_id: Any = "unknown"):
        super().__init__(
            message=f"Permission {permission_id} not found",
            error_code="permission_not_found"
        )


class PermissionExists(RBACException):
    def __init__(self, name: Any = "unknown"):
        super().__init__(
            message=f"Permission '{name}' already exists",
            error_code="permission_exists"
        )


class GrantNotAllowed(RBACException):
    def __init__(self, message: str = "You are not allowed to grant this role or permission"):
        super().__init__(
            message=message,
            error_code="grant_not_allowed"
        )


class PermissionAlreadyGranted(RBACException):
    def __init__(self, message: str = "Permission already granted"):
        super().__init__(
            message=message,
            error_code="permission_already_granted"
        )


class PermissionNotGranted(RBACException):
    def __init__(self, message: str = "Permission is not granted to this user"):
        super().__init__(
            message=message,
            error_code="permission_not_granted"
        )


class RoleAlreadyAssigned(RBACException):
    def __init__(self, message: str = "Role already assigned to this user"):
        super().__init__(
            message=message,
            error_code="role_already_assigned"
        )


class RoleNotAssigned(RBACException):
    def __init__(self, message: str = "Role is not assigned to this user"):
        super().__init__(
            message=message,
            error_code="role_not_assigned"
        )


class UnknownPermission(RBACException):
    def __init__(self, name: Any = "unknown"):
        super().__init__(
            message=f"'{name}' is not a recognized permission",
            error_code="unknown_permission"
        )


class SuperuserRequired(RBACException):
    def __init__(self, message: str = "This operation requires superuser privileges"):
        super().__init__(
            message=message,
            error_code="superuser_required"
        )
