from app.core.logger import LoggedService
from app.error.custom_exception import PermissionExists, PermissionNotFound
from app.repositories.rbac.permission import PermissionRepository
from app.schema.permission import PermissionCreate, PermissionUpdate


class PermissionService(LoggedService):
    def __init__(self, repo: PermissionRepository):
        self.repo = repo

    async def get_permission(self, permission_id: int):
        permission = await self.repo.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFound(permission_id)
        return permission

    async def create_permission(self, permission: PermissionCreate):
        existing = await self.repo.get_by_name(permission.name)
        if existing:
            raise PermissionExists(permission.name)
        return await self.repo.create(permission)

    async def update_permission(self, permission_id: int, permission_update: PermissionUpdate):
        db_permission = await self.get_permission(permission_id)
        update_data = permission_update.model_dump(exclude_unset=True)
        return await self.repo.update(db_permission, update_data)

    async def delete_permission(self, permission_id: int) -> None:
        db_permission = await self.get_permission(permission_id)
        await self.repo.delete(db_permission)

    async def get_all_permissions(self, skip: int, limit: int):
        return await self.repo.list_all(skip, limit)
