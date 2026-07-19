from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import LoggedRepository
from app.models.db_model import Permission


class PermissionRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, permission_id: int) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.id == permission_id))

    async def get_by_name(self, name: str) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.name == name))

    async def get_by_names(self, names: list[str]) -> list[Permission]:
        if not names:
            return []
        result = await self.db.scalars(select(Permission).where(Permission.name.in_(names)))
        return result.all()

    async def get_by_bit_position(self, bit_position: int) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.bit_position == bit_position))

    async def create_with_bit(self, name: str, bit_position: int) -> Permission:
        db_permission = Permission(name=name, bit_position=bit_position)
        self.db.add(db_permission)
        await self.db.commit()
        await self.db.refresh(db_permission)
        return db_permission

    async def get_by_ids(self, permission_ids: list[int]) -> list[Permission]:
        if not permission_ids:
            return []
        result = await self.db.scalars(select(Permission).where(Permission.id.in_(permission_ids)))
        return result.all()

    async def list_all(self, skip: int, limit: int) -> list[Permission]:
        result = await self.db.scalars(select(Permission).offset(skip).limit(limit))
        return result.all()
