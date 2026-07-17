import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import grant_permission_required, grant_role_required, permission_required
from app.core.dependency_factory import get_user_management_service
from app.core.logger import log_function
from app.models.db_model import User
from app.schema.user import GrantableSummary, UserDetail, UserListItem
from app.services.auth.current_user import get_current_user
from app.services.users.service import UserManagementService

router = APIRouter(tags=["Users"])


@router.get("/me/grants", response_model=GrantableSummary)
@log_function
async def get_my_grants(
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """What the logged-in user may grant to others: their effective permissions
    plus the roles/permissions their own roles are configured to delegate."""
    return await service.get_grants(current_user)


@router.get("/", response_model=list[UserListItem], dependencies=[Depends(permission_required("user:read"))])
@log_function
async def list_users(
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    skip: int = 0,
    limit: int = 20,
):
    return await service.list_users(skip, limit)


@router.get("/{user_id}", response_model=UserDetail, dependencies=[Depends(permission_required("user:read.id"))])
@log_function
async def get_user(
    user_id: uuid.UUID,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
):
    return await service.get_user_detail(user_id)


@router.post("/{user_id}/roles/{role_id}", status_code=204, dependencies=[Depends(grant_role_required())])
@log_function
async def assign_role_to_user(
    user_id: uuid.UUID,
    role_id: int,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Assign a role to a user. Only allowed if one of the caller's own roles
    is configured to be able to grant `role_id` (or the caller is a superuser)."""
    await service.assign_role(current_user, user_id, role_id)


@router.delete("/{user_id}/roles/{role_id}", status_code=204, dependencies=[Depends(grant_role_required())])
@log_function
async def remove_role_from_user(
    user_id: uuid.UUID,
    role_id: int,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await service.remove_role(current_user, user_id, role_id)


@router.post(
    "/{user_id}/permissions/{permission_id}",
    status_code=204,
    dependencies=[Depends(grant_permission_required())],
)
@log_function
async def grant_permission_to_user(
    user_id: uuid.UUID,
    permission_id: int,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Grant a single permission directly to a user, bypassing roles entirely.
    Only allowed if one of the caller's own roles is configured to be able to
    grant `permission_id` (or the caller is a superuser)."""
    await service.grant_permission(current_user, user_id, permission_id)


@router.delete(
    "/{user_id}/permissions/{permission_id}",
    status_code=204,
    dependencies=[Depends(grant_permission_required())],
)
@log_function
async def revoke_permission_from_user(
    user_id: uuid.UUID,
    permission_id: int,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await service.revoke_permission(current_user, user_id, permission_id)
