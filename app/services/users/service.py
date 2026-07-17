import uuid

from app.core.logger import LoggedService
from app.core.rbac import can_grant_permission, can_grant_role, effective_permissions
from app.error.custom_exception import (
    GrantNotAllowed,
    PermissionAlreadyGranted,
    PermissionNotFound,
    PermissionNotGranted,
    RoleAlreadyAssigned,
    RoleNotAssigned,
    RoleNotFound,
    UserNotFound,
)
from app.models.db_model import User
from app.repositories.auth.user import UserRepository
from app.repositories.rbac.permission import PermissionRepository
from app.repositories.rbac.role import RoleRepository


class UserManagementService(LoggedService):
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository, permission_repo: PermissionRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def list_users(self, skip: int, limit: int) -> list[User]:
        return await self.user_repo.list_all(skip, limit)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id_with_grants(user_id)
        if not user:
            raise UserNotFound(user_id)
        return user

    async def get_user_detail(self, user_id: uuid.UUID) -> dict:
        user = await self.get_user(user_id)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,
            "created_by_id": user.created_by_id,
            "roles": user.roles,
            "permissions": user.permissions,
            "effective_permissions": sorted(effective_permissions(user)),
        }

    async def get_grants(self, actor: User) -> dict:
        actor_role_ids = [role.id for role in actor.roles]
        if actor.is_superuser:
            grantable_roles = await self.role_repo.list_all(0, 10_000)
            grantable_permissions = await self.permission_repo.list_all(0, 10_000)
        else:
            role_ids = await self.role_repo.get_grantable_role_ids(actor_role_ids)
            permission_ids = await self.role_repo.get_grantable_permission_ids(actor_role_ids)
            grantable_roles = await self.role_repo.get_by_ids(list(role_ids))
            grantable_permissions = await self.permission_repo.get_by_ids(list(permission_ids))

        return {
            "is_superuser": actor.is_superuser,
            "effective_permissions": sorted(effective_permissions(actor)),
            "grantable_roles": grantable_roles,
            "grantable_permissions": grantable_permissions,
        }

    async def assign_role(self, actor: User, target_user_id: uuid.UUID, role_id: int) -> None:
        if not await can_grant_role(actor, role_id, self.role_repo):
            raise GrantNotAllowed(f"You are not allowed to grant role {role_id}")

        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFound(role_id)

        target = await self.user_repo.get_by_id(target_user_id)
        if not target:
            raise UserNotFound(target_user_id)

        if await self.role_repo.user_has_role(target_user_id, role_id):
            raise RoleAlreadyAssigned(f"User already has role '{role.name}'")

        await self.role_repo.assign_to_user(role_id, target_user_id)

    async def remove_role(self, actor: User, target_user_id: uuid.UUID, role_id: int) -> None:
        if not await can_grant_role(actor, role_id, self.role_repo):
            raise GrantNotAllowed(f"You are not allowed to revoke role {role_id}")

        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFound(role_id)

        target = await self.user_repo.get_by_id(target_user_id)
        if not target:
            raise UserNotFound(target_user_id)

        if not await self.role_repo.user_has_role(target_user_id, role_id):
            raise RoleNotAssigned(f"User does not have role '{role.name}'")

        await self.role_repo.remove_from_user(role_id, target_user_id)

    async def grant_permission(self, actor: User, target_user_id: uuid.UUID, permission_id: int) -> None:
        if not await can_grant_permission(actor, permission_id, self.role_repo):
            raise GrantNotAllowed(f"You are not allowed to grant permission {permission_id}")

        permission = await self.role_repo.get_permission_by_id(permission_id)
        if not permission:
            raise PermissionNotFound(permission_id)

        target = await self.user_repo.get_by_id_with_grants(target_user_id)
        if not target:
            raise UserNotFound(target_user_id)

        if await self.user_repo.has_permission(target_user_id, permission_id):
            raise PermissionAlreadyGranted(f"User already has permission '{permission.name}'")

        await self.user_repo.grant_permission(target, permission)

    async def revoke_permission(self, actor: User, target_user_id: uuid.UUID, permission_id: int) -> None:
        if not await can_grant_permission(actor, permission_id, self.role_repo):
            raise GrantNotAllowed(f"You are not allowed to revoke permission {permission_id}")

        permission = await self.role_repo.get_permission_by_id(permission_id)
        if not permission:
            raise PermissionNotFound(permission_id)

        target = await self.user_repo.get_by_id_with_grants(target_user_id)
        if not target:
            raise UserNotFound(target_user_id)

        if not await self.user_repo.has_permission(target_user_id, permission_id):
            raise PermissionNotGranted(f"User does not have permission '{permission.name}'")

        await self.user_repo.revoke_permission(target, permission)
