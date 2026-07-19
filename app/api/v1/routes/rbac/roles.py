from fastapi import APIRouter, Depends
from app.schema.rbac.role import RoleCreate, RoleUpdate, Role, RoleGrants
from typing import Annotated
from app.core.dependency_factory import get_role_service
from app.core.dependencies import permission_required
from app.core.rbac.principal import Principal
from app.models.db_model import User
from app.services.auth.current_user import get_current_user
from app.services.rbac.role_service import RoleService
from app.core.logger import log_function

router = APIRouter(tags=['Roles'])


@router.post("/", response_model=Role, status_code=201,dependencies=[Depends(permission_required("role:create"))])
@log_function
async def create_new_role(
    role: RoleCreate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await role_service.create_role(role, current_user)

@router.get("/{role_id}", response_model=Role)
@log_function
async def read_role(
    role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    principal: Annotated[Principal, Depends(permission_required("role:read.id"))],
):
    return await role_service.get_role(role_id, principal)

@router.get("/{role_id}/grants", response_model=RoleGrants)
@log_function
async def read_role_grants(
    role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    principal: Annotated[Principal, Depends(permission_required("role:read.id"))],
):
    return await role_service.get_role_grants(role_id, principal)

@router.put("/{role_id}", response_model=Role,dependencies=[Depends(permission_required("role:update"))])
@log_function
async def update_role_endpoint(
    role_id: int,
    role: RoleUpdate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await role_service.update_role(role_id, role, current_user)

@router.delete("/{role_id}", status_code=204,dependencies=[Depends(permission_required("role:delete"))])
@log_function
async def delete_role_endpoint(
    role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await role_service.delete_role(role_id, current_user)

@router.get("/", response_model=list[Role])
@log_function
async def read_roles(
    role_service: Annotated[RoleService, Depends(get_role_service)],
    principal: Annotated[Principal, Depends(permission_required("role:read"))],
    skip: int = 0,
    limit: int = 10,
):
    return await role_service.get_all_roles(principal, skip, limit)

@router.post("/{role_id}/permissions/{permission_id}", response_model=Role,dependencies=[Depends(permission_required("role:add-permission"))])
@log_function
async def add_permission_to_role_endpoint(
    role_id: int,
    permission_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await role_service.add_permission_to_role(role_id, permission_id, current_user)

@router.delete("/{role_id}/permissions/{permission_id}", response_model=Role,dependencies=[Depends(permission_required("role:delete-permission"))])
@log_function
async def remove_permission_from_role_endpoint(
    role_id: int,
    permission_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await role_service.remove_permission_from_role(role_id, permission_id, current_user)


# ----------------------------------------------------------------------
# Grant delegation configuration. Set up at role-authoring time: which
# roles/permissions a *holder* of this role is allowed to hand out to
# other users via the /users/{user_id}/roles and /permissions endpoints.
# Restricted to whoever can configure roles at all ("role:update").
# ----------------------------------------------------------------------

@router.post(
    "/{role_id}/grantable-roles/{grantable_role_id}",
    status_code=204,
    dependencies=[Depends(permission_required("role:update"))],
)
@log_function
async def add_grantable_role_endpoint(
    role_id: int,
    grantable_role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await role_service.add_grantable_role(role_id, grantable_role_id, current_user)


@router.delete(
    "/{role_id}/grantable-roles/{grantable_role_id}",
    status_code=204,
    dependencies=[Depends(permission_required("role:update"))],
)
@log_function
async def remove_grantable_role_endpoint(
    role_id: int,
    grantable_role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await role_service.remove_grantable_role(role_id, grantable_role_id, current_user)


@router.post(
    "/{role_id}/grantable-permissions/{permission_id}",
    status_code=204,
    dependencies=[Depends(permission_required("role:update"))],
)
@log_function
async def add_grantable_permission_endpoint(
    role_id: int,
    permission_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await role_service.add_grantable_permission(role_id, permission_id, current_user)


@router.delete(
    "/{role_id}/grantable-permissions/{permission_id}",
    status_code=204,
    dependencies=[Depends(permission_required("role:update"))],
)
@log_function
async def remove_grantable_permission_endpoint(
    role_id: int,
    permission_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await role_service.remove_grantable_permission(role_id, permission_id, current_user)
