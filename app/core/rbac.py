"""
Delegated-authorization helpers for the hierarchical RBAC model.

A user's permissions come from two sources: the permissions attached to
their roles, and permissions granted directly to them. Separately, a role
can be configured (by whoever creates it) with a set of "grantable" roles
and permissions — the roles/permissions a *holder* of that role is allowed
to hand out to other users. `is_superuser` bypasses every check below and
exists purely to bootstrap the first admin.
"""

from __future__ import annotations

from app.models.db_model import User
from app.repositories.rbac.role import RoleRepository


def effective_permissions(user: User) -> set[str]:
    """Union of a user's role-derived permissions and direct permission grants.

    Requires `user.roles`, each `role.permissions`, and `user.permissions` to
    already be eagerly loaded (see `UserRepository.get_by_id_with_grants`).
    """
    perms = {perm.name for role in user.roles for perm in role.permissions}
    perms.update(perm.name for perm in user.permissions)
    return perms


async def can_grant_role(actor: User, role_id: int, role_repo: RoleRepository) -> bool:
    if actor.is_superuser:
        return True
    if not actor.roles:
        return False
    grantable_ids = await role_repo.get_grantable_role_ids([role.id for role in actor.roles])
    return role_id in grantable_ids


async def can_grant_permission(actor: User, permission_id: int, role_repo: RoleRepository) -> bool:
    if actor.is_superuser:
        return True
    if not actor.roles:
        return False
    grantable_ids = await role_repo.get_grantable_permission_ids([role.id for role in actor.roles])
    return permission_id in grantable_ids
