import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import grant_permission_required, grant_role_required, permission_required
from app.core.dependency_factory import get_user_management_service
from app.core.logger import log_function
from app.core.rbac.principal import Principal
from app.models.db_model import User
from app.schema.user import GrantableSummary, UserCount, UserCreate, UserDetail, UserListItem
from app.services.auth.current_user import get_current_user
from app.services.users.user_management_service import UserManagementService

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


@router.post("/", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
@log_function
async def create_user(
    data: UserCreate,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    _principal: Annotated[Principal, Depends(permission_required("user:create"))],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Adds a new user to the caller's own tenant. `current_user` (not just
    `_principal`) is needed here because `create_user` stamps `tenant_id`/
    `created_by_id` from the real actor — same double-dependency pattern as
    role creation (`create_new_role`)."""
    return await service.create_user(current_user, data)


@router.get("/", response_model=list[UserListItem])
@log_function
async def list_users(
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    principal: Annotated[Principal, Depends(permission_required("user:read"))],
    skip: int = 0,
    limit: int = 20,
    tenant_id: uuid.UUID | None = None,
):
    return await service.list_users(
        principal.tenant_id, principal.is_superuser, skip, limit, filter_tenant_id=tenant_id
    )


@router.get("/count", response_model=UserCount)
@log_function
async def count_users(
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    principal: Annotated[Principal, Depends(permission_required("user:read"))],
    tenant_id: uuid.UUID | None = None,
):
    """Exact count, same scoping as `list_users` — for dashboard stat tiles,
    where paging through `list_users` to count would either be wasteful or
    (if capped at one page) silently wrong past the page size. Registered
    before `/{user_id}` so `count` isn't swallowed as a UUID path param."""
    count = await service.count_users(principal.tenant_id, principal.is_superuser, filter_tenant_id=tenant_id)
    return UserCount(count=count)


@router.get("/{user_id}", response_model=UserDetail)
@log_function
async def get_user(
    user_id: uuid.UUID,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    principal: Annotated[Principal, Depends(permission_required("user:read.id"))],
):
    return await service.get_user_detail(principal.tenant_id, principal.is_superuser, user_id)


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


@router.post("/{user_id}/deactivate", status_code=204)
@log_function
async def deactivate_user(
    user_id: uuid.UUID,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    principal: Annotated[Principal, Depends(permission_required("user:deactivate"))],
):
    await service.set_user_active(principal.tenant_id, principal.is_superuser, user_id, is_active=False)


@router.post("/{user_id}/activate", status_code=204)
@log_function
async def activate_user(
    user_id: uuid.UUID,
    service: Annotated[UserManagementService, Depends(get_user_management_service)],
    principal: Annotated[Principal, Depends(permission_required("user:deactivate"))],
):
    await service.set_user_active(principal.tenant_id, principal.is_superuser, user_id, is_active=True)
