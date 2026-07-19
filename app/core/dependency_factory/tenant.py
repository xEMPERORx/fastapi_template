"""Dependency wiring for the tenant domain."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependency_factory.auth import get_user_repository
from app.core.dependency_factory.rbac import get_role_repository
from app.database.postgres_db import get_db
from app.repositories.auth.user import UserRepository
from app.repositories.rbac.role import RoleRepository
from app.repositories.tenant.tenant import TenantRepository
from app.services.tenant.tenant_service import TenantService


def get_tenant_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantRepository:
    return TenantRepository(db)


def get_tenant_service(
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> TenantService:
    return TenantService(tenant_repo, role_repo, user_repo)
