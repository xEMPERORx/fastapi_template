import uuid
from typing import Optional

from app.core.logger import LoggedService
from app.core.rbac.delegation import can_grant_permission, can_grant_role, effective_permissions
from app.error.rbac import (
    GrantNotAllowed,
    PermissionAlreadyGranted,
    PermissionNotFound,
    PermissionNotGranted,
    RoleAlreadyAssigned,
    RoleNotAssigned,
    RoleNotFound,
)
from app.error.auth import UserMailExist, UsernameExist, UserNotFound
from app.models.db_model import User
from app.repositories.auth.user import UserRepository
from app.repositories.rbac.permission import PermissionRepository
from app.repositories.rbac.role import RoleRepository
from app.schema.user import UserCreate
from app.services.auth.password import get_password_hash


class UserManagementService(LoggedService):
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository, permission_repo: PermissionRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    def _ensure_same_tenant(self, target: User, tenant_id: Optional[uuid.UUID], is_superuser: bool) -> None:
        """A non-superuser actor may only see/act on a user in their own
        tenant. Raises `UserNotFound` (not a 403) so a tenant-admin probing
        another tenant's user ids learns nothing — same "don't confirm
        existence" posture as every other cross-tenant lookup here."""
        if not is_superuser and target.tenant_id != tenant_id:
            raise UserNotFound(target.id)

    async def create_user(self, actor: User, data: UserCreate) -> User:
        """Adds a new user directly to the actor's own tenant (or a global
        user, if the actor is a superuser — mirrors `actor.tenant_id` as-is,
        no special-casing needed). Gated by `user:create` at the route."""
        if await self.user_repo.exists_by_username(data.username):
            raise UsernameExist(data.username)
        if await self.user_repo.exists_by_email(data.email):
            raise UserMailExist(data.email)

        created = await self.user_repo.create(
            username=data.username,
            email=data.email,
            password=get_password_hash(data.password),
            is_verified=True,
            tenant_id=actor.tenant_id,
            created_by_id=actor.id,
        )
        # `UserListItem` serializes `.roles`; a plain `create()` leaves that
        # relationship unloaded, and Pydantic can't lazy-load it outside the
        # async context during response validation (MissingGreenlet). A
        # fresh user has none yet, but re-fetch with the same eager-load
        # used everywhere else rather than special-casing an empty list.
        return await self.user_repo.get_by_id_with_grants(created.id)

    async def list_users(
        self,
        tenant_id: Optional[uuid.UUID],
        is_superuser: bool,
        skip: int,
        limit: int,
        filter_tenant_id: Optional[uuid.UUID] = None,
    ) -> list[User]:
        """`tenant_id` is the actor's own tenant (ignored for a superuser,
        who has none). `filter_tenant_id` is an optional superuser-only
        override to view one specific tenant's users (e.g. from a tenant
        detail page) — silently ignored for a non-superuser, whose own
        `tenant_id` scoping already applies regardless of what they pass."""
        if is_superuser:
            if filter_tenant_id is not None:
                return await self.user_repo.list_by_tenant(filter_tenant_id, skip, limit)
            return await self.user_repo.list_all(skip, limit)
        return await self.user_repo.list_by_tenant(tenant_id, skip, limit)

    async def count_users(
        self, tenant_id: Optional[uuid.UUID], is_superuser: bool, filter_tenant_id: Optional[uuid.UUID] = None
    ) -> int:
        """Same scoping as `list_users`, without paying for row data — for
        dashboard stat tiles, where a `list(..., limit=N)` count would
        silently undercount past N."""
        if is_superuser:
            if filter_tenant_id is not None:
                return await self.user_repo.count_by_tenant(filter_tenant_id)
            return await self.user_repo.count_all()
        return await self.user_repo.count_by_tenant(tenant_id)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id_with_grants(user_id)
        if not user:
            raise UserNotFound(user_id)
        return user

    async def get_user_detail(self, tenant_id: Optional[uuid.UUID], is_superuser: bool, user_id: uuid.UUID) -> dict:
        user = await self.get_user(user_id)
        self._ensure_same_tenant(user, tenant_id, is_superuser)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
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
        self._ensure_same_tenant(target, actor.tenant_id, actor.is_superuser)

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
        self._ensure_same_tenant(target, actor.tenant_id, actor.is_superuser)

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
        self._ensure_same_tenant(target, actor.tenant_id, actor.is_superuser)

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
        self._ensure_same_tenant(target, actor.tenant_id, actor.is_superuser)

        if not await self.user_repo.has_permission(target_user_id, permission_id):
            raise PermissionNotGranted(f"User does not have permission '{permission.name}'")

        await self.user_repo.revoke_permission(target, permission)

    async def set_user_active(
        self, tenant_id: Optional[uuid.UUID], is_superuser: bool, target_user_id: uuid.UUID, is_active: bool
    ) -> None:
        """Immediately blocks (or restores) a user's ability to authenticate
        via the authz cache's inactive-user set — see `app.core.authz_cache`
        — rather than only through the coarser tenant-wide deactivation."""
        target = await self.user_repo.get_by_id(target_user_id)
        if not target:
            raise UserNotFound(target_user_id)
        self._ensure_same_tenant(target, tenant_id, is_superuser)
        await self.user_repo.set_active(target, is_active)
