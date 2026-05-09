from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import LoggedRepository
from app.models.db_model import Permission
from app.schema.permission import PermissionCreate


class PermissionRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, permission_id: int) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.id == permission_id))

    async def get_by_name(self, name: str) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.name == name))

    async def create(self, permission: PermissionCreate) -> Permission:
        db_permission = Permission(name=permission.name)
        self.db.add(db_permission)
        await self.db.commit()
        await self.db.refresh(db_permission)
        return db_permission

    async def update(self, permission: Permission, update_data: dict) -> Permission:
        for key, value in update_data.items():
            setattr(permission, key, value)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def delete(self, permission: Permission) -> None:
        await self.db.delete(permission)
        await self.db.commit()

    async def list_all(self, skip: int, limit: int) -> list[Permission]:
        result = await self.db.scalars(select(Permission).offset(skip).limit(limit))
        return result.all()
