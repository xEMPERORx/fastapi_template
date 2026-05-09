from fastapi import APIRouter, Depends
from app.schema.permission import PermissionCreate, PermissionUpdate, PermissionResponse
from typing import Annotated
from app.core.dependency_factory import get_permission_service
from app.core.dependencies import permission_required
from app.services.permission.service import PermissionService
from app.core.logger import log_function


router = APIRouter(tags=['Permissions'])

@router.post("/", response_model=PermissionResponse, status_code=201,dependencies=[Depends(permission_required("permission:create"))])
@log_function
async def create_new_permission(
    permission: PermissionCreate,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    return await permission_service.create_permission(permission)

@router.get("/{permission_id}", response_model=PermissionResponse,dependencies=[Depends(permission_required("permission:read.id"))])
@log_function
async def read_permission(
    permission_id: int,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    return await permission_service.get_permission(permission_id)

@router.put("/{permission_id}", response_model=PermissionResponse,dependencies=[Depends(permission_required("permission:update"))])
@log_function
async def update_permission_endpoint(
    permission_id: int,
    permission: PermissionUpdate,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    return await permission_service.update_permission(permission_id, permission)

@router.delete("/{permission_id}", status_code=204,dependencies=[Depends(permission_required("permission:delete"))])
@log_function
async def delete_permission_endpoint(
    permission_id: int,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    return await permission_service.delete_permission(permission_id)

@router.get("/", response_model=list[PermissionResponse],dependencies=[Depends(permission_required("permission:read"))])
@log_function
async def read_permissions(
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    skip: int = 0,
    limit: int = 10,
):
    return await permission_service.get_all_permissions(skip, limit)
