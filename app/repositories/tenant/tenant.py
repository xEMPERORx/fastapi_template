import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz_cache import publish_events
from app.core.logger import LoggedRepository
from app.models.db_model import Tenant


class TenantRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        return await self.db.scalar(select(Tenant).where(Tenant.id == tenant_id))

    async def get_by_name(self, name: str) -> Tenant | None:
        return await self.db.scalar(select(Tenant).where(Tenant.name == name))

    async def create(self, name: str, allowed_permission_mask: int = 0) -> Tenant:
        tenant = Tenant(name=name, allowed_permission_mask=allowed_permission_mask)
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def list_all(self, skip: int, limit: int) -> list[Tenant]:
        result = await self.db.scalars(select(Tenant).offset(skip).limit(limit))
        return result.all()

    async def set_allowed_permission_mask(self, tenant: Tenant, mask: int) -> Tenant:
        tenant.allowed_permission_mask = mask
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def set_active(self, tenant: Tenant, is_active: bool) -> Tenant:
        tenant.is_active = is_active
        await self.db.commit()
        await self.db.refresh(tenant)
        await publish_events([
            {"type": "tenant_status", "tenant_id": str(tenant.id), "is_active": is_active}
        ])
        return tenant
