from pydantic import BaseModel, ConfigDict, Field

from app.core.validation import SafeIdentifier

class PermissionBase(BaseModel):
    name: SafeIdentifier = Field(min_length=1, max_length=100)

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    model_config = ConfigDict(from_attributes=True) 
    id: int
