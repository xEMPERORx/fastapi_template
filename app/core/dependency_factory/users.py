"""Dependency wiring for user-management endpoints (admin-facing user CRUD,
role/permission assignment) — pulls repository factories from the auth and
rbac dependency modules since a user's roles/permissions span both domains.
"""

from typing import Annotated

from fastapi import Depends

from app.core.dependency_factory.auth import get_user_repository
from app.core.dependency_factory.rbac import get_permission_repository, get_role_repository
from app.repositories.auth.user import UserRepository
from app.repositories.rbac.permission import PermissionRepository
from app.repositories.rbac.role import RoleRepository
from app.services.users.user_management_service import UserManagementService


def get_user_management_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)],
    permission_repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
) -> UserManagementService:
    return UserManagementService(user_repo, role_repo, permission_repo)
