from app.core.logger import LoggedService
from app.error.rbac import PermissionNotFound
from app.repositories.rbac.permission import PermissionRepository


class PermissionService(LoggedService):
    def __init__(self, repo: PermissionRepository):
        self.repo = repo

    async def get_permission(self, permission_id: int):
        permission = await self.repo.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFound(permission_id)
        return permission

    async def get_all_permissions(self, skip: int, limit: int):
        return await self.repo.list_all(skip, limit)
