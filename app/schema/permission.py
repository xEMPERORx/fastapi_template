from pydantic import BaseModel, ConfigDict

class PermissionBase(BaseModel):
    name: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    model_config = ConfigDict(from_attributes=True) 
    id: int
