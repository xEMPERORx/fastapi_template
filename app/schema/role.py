from pydantic import BaseModel,field_validator,ConfigDict
from typing import List

class RoleBase(BaseModel):
    name: str

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
