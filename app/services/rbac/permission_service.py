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

    async def get_all_permissions(self, skip: int, limit: int, names: list[str] | None = None):
        """`names=None` returns the full catalog (superuser). Otherwise
        restricted to exactly that set — see `read_permissions` in
        `app/api/v1/routes/rbac/permission.py` for why a non-superuser only
        ever passes their own effective permission names."""
        if names is None:
            return await self.repo.list_all(skip, limit)
        return await self.repo.list_by_names(names, skip, limit)
