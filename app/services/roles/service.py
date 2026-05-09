import uuid

from fastapi import HTTPException

from app.core.logger import LoggedService
from app.repositories.rbac.role import RoleRepository
from app.schema.role import RoleCreate, RoleUpdate


class RoleService(LoggedService):
    def __init__(self, repo: RoleRepository):
        self.repo = repo

    async def get_role(self, role_id: int):
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    async def create_role(self, role: RoleCreate):
        existing = await self.repo.get_by_name(role.name)
        if existing:
            raise HTTPException(status_code=400, detail="Role already exists")
        return await self.repo.create(role)

    async def update_role(self, role_id: int, role_update: RoleUpdate):
        db_role = await self.get_role(role_id)
        update_data = role_update.model_dump(exclude_unset=True)
        return await self.repo.update(db_role, update_data)

    async def delete_role(self, role_id: int):
        db_role = await self.get_role(role_id)
        await self.repo.delete(db_role)

    async def get_all_roles(self, skip: int, limit: int):
        return await self.repo.list_all(skip, limit)

    async def assign_role_user(self, role_id: int, user_id: uuid.UUID):
        await self.repo.assign_to_user(role_id, user_id)

    async def add_permission_to_role(self, role_id: int, permission_id: int):
        role = await self.get_role(role_id)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise HTTPException(status_code=404, detail="Permission not found")
        if perm in role.permissions:
            raise HTTPException(status_code=400, detail="Permission already assigned to role")
        return await self.repo.add_permission(role, perm)

    async def remove_permission_from_role(self, role_id: int, permission_id: int):
        role = await self.get_role(role_id)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise HTTPException(status_code=404, detail="Permission not found")
        if perm not in role.permissions:
            raise HTTPException(status_code=400, detail="Permission not associated with this role")
        return await self.repo.remove_permission(role, perm)
