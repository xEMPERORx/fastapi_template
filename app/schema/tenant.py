import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.security.validation import SafeIdentifier, SafeStr, StrongPassword


class TenantCreate(BaseModel):
    name: SafeIdentifier
    admin_username: SafeStr
    admin_email: EmailStr
    admin_password: StrongPassword
    # Ceiling on what this tenant's roles may ever hold. Omit (or pass null)
    # to grant every non-superuser-only permission — the previous, only
    # behavior. Anything outside `TENANT_ROLE_MASK` (e.g. `tenant:create`) is
    # silently clamped off by `TenantService`, not rejected — a superuser
    # picking "everything" in a UI checkbox list shouldn't have to know which
    # boxes are secretly inert.
    allowed_permissions: Optional[List[SafeIdentifier]] = None


class TenantPermissionsUpdate(BaseModel):
    allowed_permissions: List[SafeIdentifier]


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    allowed_permissions: List[str]

    model_config = ConfigDict(from_attributes=True)


class TenantAdminResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TenantWithAdminResponse(BaseModel):
    tenant: TenantResponse
    admin: TenantAdminResponse
