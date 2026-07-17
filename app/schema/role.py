from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import List

from app.core.validation import SafeIdentifier

class RoleBase(BaseModel):
    name: SafeIdentifier = Field(min_length=1, max_length=100)

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass


class Role(RoleBase):
    id: int
    permissions: List[str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator('permissions', mode='before')
    @classmethod
    def convert_permissions_to_strings(cls, v):
        return [p.name if hasattr(p, 'name') else p for p in v]


class RoleGrants(BaseModel):
    """What a holder of this role is configured to be able to hand out to other users."""
    grantable_roles: List[str]
    grantable_permissions: List[str]
