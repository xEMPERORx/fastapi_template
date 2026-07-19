from app.core.logger import LoggedService
from app.core.rbac.registry import expand_implied, mask_for
from app.error.rbac import (
    GrantNotAllowed,
    PermissionAlreadyGranted,
    PermissionNotFound,
    PermissionNotGranted,
    RoleExists,
    RoleNotFound,
)
from app.models.db_model import User
from app.repositories.rbac.permission import PermissionRepository
from app.repositories.rbac.role import RoleRepository
from app.schema.rbac.role import RoleCreate, RoleUpdate


class RoleService(LoggedService):
    def __init__(self, repo: RoleRepository, permission_repo: PermissionRepository):
        self.repo = repo
        self.permission_repo = permission_repo

    def _ensure_role_in_scope(self, role, actor) -> None:
        """A non-superuser actor may only see/mutate a role that's global
        (tenant_id is None — e.g. a seed role available everywhere) or
        belongs to their own tenant. Prevents a tenant admin from reading or
        editing another tenant's roles even if they somehow learn its id.
        `actor` is duck-typed (`User` or the zero-DB `Principal`) — only
        `.is_superuser`/`.tenant_id` are read."""
        if actor.is_superuser:
            return
        if role.tenant_id is not None and role.tenant_id != actor.tenant_id:
            raise RoleNotFound(role.id)

    async def get_role(self, role_id: int, actor):
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise RoleNotFound(role_id)
        self._ensure_role_in_scope(role, actor)
        return role

    async def create_role(self, role: RoleCreate, actor: User):
        """Create a role scoped to the actor's tenant (or global, for a
        superuser). Requested permission names are expanded through
        `expand_implied` first — e.g. requesting only `role:update` also
        grants `role:read`/`role:read.id`, resolved here (once, at authoring
        time) rather than as a runtime hierarchy every request would have to
        walk. A non-superuser actor may only request (post-expansion)
        permissions that are a subset of what their own roles are configured
        to grant — `requested_mask & ~allowed_mask` is non-zero exactly when
        the request asks for a permission outside that set, generalizing the
        same per-permission check `can_grant_permission` already does for
        assignment, applied here to authoring instead.

        The actor's own roles are auto-linked as able to grant the new role
        (`role_grantable_roles`) so a tenant admin who creates a role isn't
        left unable to assign it to anyone, including themselves.
        """
        tenant_id = None if actor.is_superuser else actor.tenant_id
        existing = await self.repo.get_by_name(role.name, tenant_id=tenant_id)
        if existing:
            raise RoleExists(role.name)

        expanded_names = expand_implied(role.permission_names)
        requested_mask = mask_for(expanded_names)

        if not actor.is_superuser:
            actor_role_ids = [r.id for r in actor.roles]
            allowed_mask = await self.repo.get_grantable_permission_mask(actor_role_ids)
            if requested_mask & ~allowed_mask:
                raise GrantNotAllowed("Requested permissions exceed what you are allowed to grant")

        permissions = await self.permission_repo.get_by_names(list(expanded_names))
        new_role = await self.repo.create(
            role, tenant_id=tenant_id, permissions=permissions, permission_mask=requested_mask
        )

        if not actor.is_superuser:
            for actor_role in actor.roles:
                if not await self.repo.grantable_role_link_exists(actor_role.id, new_role.id):
                    await self.repo.add_grantable_role(actor_role.id, new_role.id)

        return new_role

    async def update_role(self, role_id: int, role_update: RoleUpdate, actor: User):
        db_role = await self.get_role(role_id, actor)
        update_data = role_update.model_dump(exclude_unset=True)
        return await self.repo.update(db_role, update_data)

    async def delete_role(self, role_id: int, actor: User):
        db_role = await self.get_role(role_id, actor)
        await self.repo.delete(db_role)

    async def get_all_roles(self, actor, skip: int, limit: int):
        if actor.is_superuser:
            return await self.repo.list_all(skip, limit)
        return await self.repo.list_by_tenant(actor.tenant_id, skip, limit)

    async def add_permission_to_role(self, role_id: int, permission_id: int, actor: User):
        """Adding one permission also adds whatever it implies
        (`expand_implied`) that the role doesn't already have — same
        write-time expansion `create_role` does, just for an already-existing
        role instead of a brand-new one."""
        role = await self.get_role(role_id, actor)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(permission_id)
        if perm in role.permissions:
            raise PermissionAlreadyGranted("Permission already assigned to role")

        have_names = {p.name for p in role.permissions}
        implied_names = expand_implied([perm.name]) - have_names - {perm.name}
        implied_perms = await self.permission_repo.get_by_names(list(implied_names)) if implied_names else []

        role = await self.repo.add_permission(role, perm)
        for implied_perm in implied_perms:
            role = await self.repo.add_permission(role, implied_perm)
        return role

    async def remove_permission_from_role(self, role_id: int, permission_id: int, actor: User):
        role = await self.get_role(role_id, actor)
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

    async def add_grantable_role(self, role_id: int, grantable_role_id: int, actor: User) -> None:
        await self.get_role(role_id, actor)
        grantable_role = await self.repo.get_by_id(grantable_role_id)
        if not grantable_role:
            raise RoleNotFound(grantable_role_id)
        if await self.repo.grantable_role_link_exists(role_id, grantable_role_id):
            raise PermissionAlreadyGranted(
                f"Role '{grantable_role.name}' is already grantable by this role"
            )
        await self.repo.add_grantable_role(role_id, grantable_role_id)

    async def remove_grantable_role(self, role_id: int, grantable_role_id: int, actor: User) -> None:
        await self.get_role(role_id, actor)
        grantable_role = await self.repo.get_by_id(grantable_role_id)
        if not grantable_role:
            raise RoleNotFound(grantable_role_id)
        if not await self.repo.grantable_role_link_exists(role_id, grantable_role_id):
            raise PermissionNotGranted(
                f"Role '{grantable_role.name}' is not configured as grantable by this role"
            )
        await self.repo.remove_grantable_role(role_id, grantable_role_id)

    async def add_grantable_permission(self, role_id: int, permission_id: int, actor: User) -> None:
        await self.get_role(role_id, actor)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(permission_id)
        if await self.repo.grantable_permission_link_exists(role_id, permission_id):
            raise PermissionAlreadyGranted(
                f"Permission '{perm.name}' is already grantable by this role"
            )
        await self.repo.add_grantable_permission(role_id, permission_id)

    async def remove_grantable_permission(self, role_id: int, permission_id: int, actor: User) -> None:
        await self.get_role(role_id, actor)
        perm = await self.repo.get_permission_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(permission_id)
        if not await self.repo.grantable_permission_link_exists(role_id, permission_id):
            raise PermissionNotGranted(
                f"Permission '{perm.name}' is not configured as grantable by this role"
            )
        await self.repo.remove_grantable_permission(role_id, permission_id)

    async def get_role_grants(self, role_id: int, actor) -> dict:
        await self.get_role(role_id, actor)
        grantable_role_ids = await self.repo.get_grantable_role_ids([role_id])
        grantable_permission_ids = await self.repo.get_grantable_permission_ids([role_id])
        grantable_roles = await self.repo.get_by_ids(list(grantable_role_ids))
        grantable_permissions = await self.permission_repo.get_by_ids(list(grantable_permission_ids))
        return {
            "grantable_roles": [role.name for role in grantable_roles],
            "grantable_permissions": [perm.name for perm in grantable_permissions],
        }
