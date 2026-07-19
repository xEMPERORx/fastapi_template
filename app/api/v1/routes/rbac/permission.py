from fastapi import APIRouter, Depends
from app.schema.rbac.permission import PermissionResponse
from typing import Annotated
from app.core.dependency_factory import get_permission_service
from app.core.dependencies import permission_required
from app.services.rbac.permission_service import PermissionService
from app.core.logger import log_function


router = APIRouter(tags=['Permissions'])

# Permissions are code-defined (see `app.core.rbac.registry`) and mirrored
# into this table by `app/cli/sync_permissions.py` on every startup — there
# is deliberately no create/update/delete here. Inventing a Permission row
# outside the registry has no bit position, so it could never be OR'd into
# any mask: it would look real in a list but grant nothing. Add a new
# permission by adding a line to `PERMISSION_REGISTRY` and redeploying.

@router.get("/{permission_id}", response_model=PermissionResponse,dependencies=[Depends(permission_required("permission:read.id"))])
@log_function
async def read_permission(
    permission_id: int,
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
):
    return await permission_service.get_permission(permission_id)

@router.get("/", response_model=list[PermissionResponse],dependencies=[Depends(permission_required("permission:read"))])
@log_function
async def read_permissions(
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    skip: int = 0,
    limit: int = 10,
):
    return await permission_service.get_all_permissions(skip, limit)
