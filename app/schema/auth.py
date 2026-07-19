import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.security.validation import SafeStr, StrongPassword


class UserRegister(BaseModel):
    username: SafeStr = Field(min_length=3, max_length=50)
    email: EmailStr
    password: StrongPassword


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    tenant_id: Optional[uuid.UUID] = None
    tenant_name: Optional[str] = None
    is_superuser: bool = False

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class UserRegisterResponse(BaseModel):
    message: str
    user: UserResponse

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class UserPasswordReset(BaseModel):
    email: EmailStr


class UserNewPassword(BaseModel):
    new_password: str
    confirm_password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    """The access token's claims. Explicit/typed (rather than a raw dict)
    so encode/decode share one contract — see `app.services.auth.token`.

    `perm_mask` is the hex-encoded 256-bit effective permission mask (see
    `app.core.rbac.mask`), computed once at mint time (login/refresh) from
    the user's roles + direct grants. `perm_version` is compared against
    the authz cache's live version for this user (see
    `app.core.authz_cache`) to detect a stale mask without re-querying the
    DB on every request. `is_superuser` has to be its own claim rather than
    folded into `perm_mask` — the superuser bypass short-circuits checks
    (grant-delegation, role-name gates) that aren't expressible as catalog
    permission bits at all.
    """

    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    is_superuser: bool = False
    perm_mask: str
    perm_version: int
    exp: datetime
    auth_method: str = "password"

    model_config = ConfigDict(from_attributes=True)


class GoogleAuthUrlResponse(BaseModel):
    authorization_url: str
    state: str


class GoogleOAuthCallbackResponse(TokenResponse):
    user: UserResponse
    is_new_user: bool
