import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security.validation import SafeStr, StrongPassword
from app.schema.auth import (
    GoogleAuthUrlResponse,
    GoogleOAuthCallbackResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLogin,
    UserNewPassword,
    UserPasswordReset,
    UserRegister,
    UserRegisterResponse,
    UserResponse,
)

__all__ = [
    "GoogleAuthUrlResponse",
    "GoogleOAuthCallbackResponse",
    "TokenRefreshRequest",
    "TokenResponse",
    "UserLogin",
    "UserNewPassword",
    "UserPasswordReset",
    "UserRegister",
    "UserRegisterResponse",
    "UserResponse",
    "RoleSummary",
    "PermissionSummary",
    "UserListItem",
    "UserDetail",
    "GrantableSummary",
    "UserCreate",
    "UserCount",
]


def _names(v):
    return [item.name if hasattr(item, "name") else item for item in v]


class RoleSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PermissionSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserListItem(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    is_verified: bool
    is_superuser: bool
    is_active: bool
    created_by_id: Optional[uuid.UUID] = None
    roles: List[str] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("roles", mode="before")
    @classmethod
    def _role_names(cls, v):
        return _names(v)


class UserDetail(UserListItem):
    permissions: List[str] = []
    effective_permissions: List[str] = []

    @field_validator("permissions", mode="before")
    @classmethod
    def _permission_names(cls, v):
        return _names(v)


class GrantableSummary(BaseModel):
    is_superuser: bool
    effective_permissions: List[str]
    grantable_roles: List[RoleSummary]
    grantable_permissions: List[PermissionSummary]


class UserCount(BaseModel):
    count: int


class UserCreate(BaseModel):
    """A tenant-admin (or anyone holding `user:create`) adding a new user to
    their own tenant — distinct from `UserRegister`, which always creates a
    global (`tenant_id = NULL`) self-service account. The actor's tenant is
    applied server-side (`UserManagementService.create_user`); this schema
    deliberately has no `tenant_id` field, same rationale as `is_superuser`
    being absent from every request schema — never let the caller pick a
    tenant to write into."""

    username: SafeStr = Field(min_length=3, max_length=50)
    email: EmailStr
    password: StrongPassword
