"""Exceptions raised by the tenant domain (see `app.services.tenant`)."""

from typing import Any

from app.error.base import AppException


class TenantException(AppException):
    pass


class TenantNotFound(TenantException):
    def __init__(self, tenant_id: Any = "unknown"):
        super().__init__(
            message=f"Tenant {tenant_id} not found",
            error_code="tenant_not_found"
        )


class TenantExists(TenantException):
    def __init__(self, name: Any = "unknown"):
        super().__init__(
            message=f"Tenant '{name}' already exists",
            error_code="tenant_exists"
        )
