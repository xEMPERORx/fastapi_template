import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import superuser_required
from app.core.dependency_factory import get_tenant_service
from app.core.logger import log_function
from app.models.db_model import User
from app.schema.tenant import TenantCreate, TenantResponse, TenantWithAdminResponse
from app.services.tenant.tenant_service import TenantService

router = APIRouter(tags=["Tenants"])


@router.post("/", response_model=TenantWithAdminResponse, status_code=status.HTTP_201_CREATED)
@log_function
async def create_tenant(
    data: TenantCreate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[User, Depends(superuser_required())],
):
    return await service.create_tenant_with_admin(current_user, data)


@router.get("/", response_model=list[TenantResponse])
@log_function
async def list_tenants(
    service: Annotated[TenantService, Depends(get_tenant_service)],
    _current_user: Annotated[User, Depends(superuser_required())],
    skip: int = 0,
    limit: int = 20,
):
    return await service.list_tenants(skip, limit)


@router.get("/{tenant_id}", response_model=TenantResponse)
@log_function
async def get_tenant(
    tenant_id: uuid.UUID,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    _current_user: Annotated[User, Depends(superuser_required())],
):
    return await service.get_tenant(tenant_id)


@router.post("/{tenant_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
@log_function
async def deactivate_tenant(
    tenant_id: uuid.UUID,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[User, Depends(superuser_required())],
):
    await service.set_tenant_active(current_user, tenant_id, is_active=False)


@router.post("/{tenant_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
@log_function
async def activate_tenant(
    tenant_id: uuid.UUID,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[User, Depends(superuser_required())],
):
    await service.set_tenant_active(current_user, tenant_id, is_active=True)
