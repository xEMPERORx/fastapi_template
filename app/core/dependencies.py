from typing import List

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac.delegation import can_grant_permission, can_grant_role
from app.core.rbac.principal import Principal
from app.core.rbac.registry import PERMISSION_REGISTRY
from app.database.postgres_db import get_db
from app.error.rbac import GrantNotAllowed, SuperuserRequired
from app.models.db_model import User
from app.repositories.rbac.role import RoleRepository
from app.services.auth.current_user import get_current_principal, get_current_user


def role_required(roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.is_superuser:
            return current_user
        if not any(role.name in roles for role in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker


def permission_required(required_permission: str):
    """Mask-based, zero-DB-query gate: `get_current_principal` decodes the
    JWT and checks the authz cache (`app.core.authz_cache`) for a
    deactivated user/tenant or a stale mask, then this just tests one bit.
    `PERMISSION_REGISTRY[...]` is looked up here, at route-decoration time
    (import time) rather than per-request, so a typo'd permission string
    fails immediately on startup, not on a random future request."""
    bit = PERMISSION_REGISTRY[required_permission]

    def permission_checker(principal: Principal = Depends(get_current_principal)):
        if principal.is_superuser:
            return principal
        if not (principal.perm_mask & (1 << bit)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_permission}"
            )
        return principal
    return permission_checker


def grant_role_required():
    """
    Gate an endpoint that assigns a `role_id` path param to a user, based on
    the acting user's role-delegation configuration (`Role.grantable_roles`)
    rather than a fixed permission string — because "can I grant this" is
    data-dependent (which role, configured by whoever created it).
    """
    async def checker(
        role_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        role_repo = RoleRepository(db)
        if not await can_grant_role(current_user, role_id, role_repo):
            raise GrantNotAllowed(f"You are not allowed to grant role {role_id}")
        return current_user
    return checker


def grant_permission_required():
    """Gate an endpoint that grants a `permission_id` path param directly to a user."""
    async def checker(
        permission_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        role_repo = RoleRepository(db)
        if not await can_grant_permission(current_user, permission_id, role_repo):
            raise GrantNotAllowed(f"You are not allowed to grant permission {permission_id}")
        return current_user
    return checker


def superuser_required():
    """Gate an endpoint that must never be reachable via any catalog
    permission — e.g. creating a tenant. Unlike `permission_required`, there
    is no permission string that can substitute for this: mirrors
    `app/cli/seed.py`'s "escape hatch, never via a grantable permission"
    philosophy for `is_superuser` itself.
    """
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_superuser:
            raise SuperuserRequired()
        return current_user
    return checker
