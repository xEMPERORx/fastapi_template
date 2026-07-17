from app.core.logger import LoggedService
from app.error.custom_exception import (
    PermissionAlreadyGranted,
    PermissionNotFound,
    PermissionNotGranted,
    RoleExists,
    RoleNotFound,
)
from app.repositories.rbac.permission import PermissionRepository
from app.repositories.rbac.role import RoleRepository
from app.schema.role import RoleCreate, RoleUpdate


class RoleService(LoggedService):
    def __init__(self, repo: RoleRepository, permission_repo: PermissionRepository):
        self.repo = repo
        self.permission_repo = permission_repo

    async def get_role(self, role_id: int):
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise RoleNotFound(role_id)
        return role

    async def create_role(self, role: RoleCreate):
        existing = await self.repo.get_by_name(role.name)
        if existing:
            raise RoleExists(role.name)
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

    async def add_permission_to_role(self, role_id: int, permission_id: int):
        role = await self.get_role(role_id)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(permission_id)
        if perm in role.permissions:
            raise PermissionAlreadyGranted("Permission already assigned to role")
        return await self.repo.add_permission(role, perm)

    async def remove_permission_from_role(self, role_id: int, permission_id: int):
        role = await self.get_role(role_id)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(permission_id)
        if perm not in role.permissions:
            raise PermissionNotGranted("Permission not associated with this role")
        return await self.repo.remove_permission(role, perm)

    # ------------------------------------------------------------------
    # Grant delegation configuration: which roles/permissions a holder of
    # `role_id` may hand out to other users. Configured by whoever authors
    # the role.
    # ------------------------------------------------------------------

    async def add_grantable_role(self, role_id: int, grantable_role_id: int) -> None:
        await self.get_role(role_id)
        grantable_role = await self.repo.get_by_id(grantable_role_id)
        if not grantable_role:
            raise RoleNotFound(grantable_role_id)
        if await self.repo.grantable_role_link_exists(role_id, grantable_role_id):
            raise PermissionAlreadyGranted(
                f"Role '{grantable_role.name}' is already grantable by this role"
            )
        await self.repo.add_grantable_role(role_id, grantable_role_id)

    async def remove_grantable_role(self, role_id: int, grantable_role_id: int) -> None:
        await self.get_role(role_id)
        grantable_role = await self.repo.get_by_id(grantable_role_id)
        if not grantable_role:
            raise RoleNotFound(grantable_role_id)
        if not await self.repo.grantable_role_link_exists(role_id, grantable_role_id):
            raise PermissionNotGranted(
                f"Role '{grantable_role.name}' is not configured as grantable by this role"
            )
        await self.repo.remove_grantable_role(role_id, grantable_role_id)

    async def add_grantable_permission(self, role_id: int, permission_id: int) -> None:
        await self.get_role(role_id)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(permission_id)
        if await self.repo.grantable_permission_link_exists(role_id, permission_id):
            raise PermissionAlreadyGranted(
                f"Permission '{perm.name}' is already grantable by this role"
            )
        await self.repo.add_grantable_permission(role_id, permission_id)

    async def remove_grantable_permission(self, role_id: int, permission_id: int) -> None:
        await self.get_role(role_id)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(permission_id)
        if not await self.repo.grantable_permission_link_exists(role_id, permission_id):
            raise PermissionNotGranted(
                f"Permission '{perm.name}' is not configured as grantable by this role"
            )
        await self.repo.remove_grantable_permission(role_id, permission_id)

    async def get_role_grants(self, role_id: int) -> dict:
        await self.get_role(role_id)
        grantable_role_ids = await self.repo.get_grantable_role_ids([role_id])
        grantable_permission_ids = await self.repo.get_grantable_permission_ids([role_id])
        grantable_roles = await self.repo.get_by_ids(list(grantable_role_ids))
        grantable_permissions = await self.permission_repo.get_by_ids(list(grantable_permission_ids))
        return {
            "grantable_roles": [role.name for role in grantable_roles],
            "grantable_permissions": [perm.name for perm in grantable_permissions],
        }
