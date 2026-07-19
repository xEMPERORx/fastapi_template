import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.security.validation import SafeIdentifier, SafeStr, StrongPassword


class TenantCreate(BaseModel):
    name: SafeIdentifier
    admin_username: SafeStr
    admin_email: EmailStr
    admin_password: StrongPassword


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TenantAdminResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TenantWithAdminResponse(BaseModel):
    tenant: TenantResponse
    admin: TenantAdminResponse
