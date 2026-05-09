from fastapi import APIRouter, Depends
from app.schema.role import RoleCreate, RoleUpdate, Role
from typing import Annotated
from app.core.dependency_factory import get_role_service
import uuid
from app.core.dependencies import permission_required
from app.services.roles.service import RoleService
from app.core.logger import log_function

router = APIRouter(tags=['Roles'])


@router.post("/", response_model=Role, status_code=201,dependencies=[Depends(permission_required("role:create"))])
@log_function
async def create_new_role(
    role: RoleCreate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
):
    return await role_service.create_role(role)

@router.get("/{role_id}", response_model=Role,dependencies=[Depends(permission_required("role:read.id"))])
@log_function
async def read_role(
    role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
):
    return await role_service.get_role(role_id)

@router.get("/{user_id}/assign/{role_id}" , dependencies=[Depends(permission_required("role:add:user"))])
@log_function
async def add_role(
    role_id:int,
    user_id:uuid.UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
):
    return await role_service.assign_role_user(role_id, user_id)

@router.put("/{role_id}", response_model=Role,dependencies=[Depends(permission_required("role:update"))])
@log_function
async def update_role_endpoint(
    role_id: int,
    role: RoleUpdate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
):
    return await role_service.update_role(role_id, role)

@router.delete("/{role_id}", status_code=204,dependencies=[Depends(permission_required("role:delete"))])
@log_function
async def delete_role_endpoint(
    role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
):
    await role_service.delete_role(role_id)

@router.get("/", response_model=list[Role],dependencies=[Depends(permission_required("role:read"))])
@log_function
async def read_roles(
    role_service: Annotated[RoleService, Depends(get_role_service)],
    skip: int = 0,
    limit: int = 10,
):
    return await role_service.get_all_roles(skip, limit)

@router.post("/{role_id}/permissions/{permission_id}", response_model=Role,dependencies=[Depends(permission_required("role:add-permission"))])
@log_function
async def add_permission_to_role_endpoint(
    role_id: int,
    permission_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
):
    return await role_service.add_permission_to_role(role_id, permission_id)

@router.delete("/{role_id}/permissions/{permission_id}", response_model=Role,dependencies=[Depends(permission_required("role:delete-permission"))])
@log_function
async def remove_permission_from_role_endpoint(
    role_id: int,
    permission_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
):
    return await role_service.remove_permission_from_role(role_id, permission_id)
