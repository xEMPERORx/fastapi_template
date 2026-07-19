"""Dependency wiring for the RBAC domain: role/permission repositories and services."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres_db import get_db
from app.repositories.rbac.permission import PermissionRepository
from app.repositories.rbac.role import RoleRepository
from app.services.rbac.permission_service import PermissionService
from app.services.rbac.role_service import RoleService


def get_role_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleRepository:
    return RoleRepository(db)


def get_permission_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PermissionRepository:
    return PermissionRepository(db)


def get_role_service(
    repo: Annotated[RoleRepository, Depends(get_role_repository)],
    permission_repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
) -> RoleService:
    return RoleService(repo, permission_repo)


def get_permission_service(
    repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
) -> PermissionService:
    return PermissionService(repo)
