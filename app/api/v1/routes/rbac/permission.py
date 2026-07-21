from fastapi import APIRouter, Depends
from app.core.rbac.registry import names_for_mask
from app.schema.rbac.permission import PermissionResponse
from typing import Annotated
from app.core.dependency_factory import get_permission_service
from app.core.dependencies import permission_required
from app.core.rbac.principal import Principal
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

@router.get("/", response_model=list[PermissionResponse])
@log_function
async def read_permissions(
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    principal: Annotated[Principal, Depends(permission_required("permission:read"))],
    skip: int = 0,
    limit: int = 10,
):
    """A superuser sees the whole catalog. Everyone else sees only the
    permissions actually held in their own effective mask — a tenant admin
    (or any role holder) shouldn't see the wider catalog of permissions that
    exist on the deployment but were never granted to them."""
    names = None if principal.is_superuser else names_for_mask(principal.perm_mask)
    return await permission_service.get_all_permissions(skip, limit, names)
