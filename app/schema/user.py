import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

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
