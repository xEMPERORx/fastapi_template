import uuid

from sqlalchemy import delete, exists, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logger import LoggedRepository
from app.models.db_model import (
    Permission,
    Role,
    role_grantable_permissions,
    role_grantable_roles,
    user_roles,
)
from app.schema.role import RoleCreate


class RoleRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: int) -> Role | None:
        return await self.db.scalar(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )

    async def get_by_name(self, name: str) -> Role | None:
        return await self.db.scalar(select(Role).where(Role.name == name))

    async def get_by_ids(self, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []
        result = await self.db.scalars(
            select(Role).options(selectinload(Role.permissions)).where(Role.id.in_(role_ids))
        )
        return result.unique().all()

    async def create(self, role: RoleCreate) -> Role:
        db_role = Role(name=role.name)
        self.db.add(db_role)
        await self.db.commit()
        await self.db.refresh(db_role)
        return await self.get_by_id(db_role.id)

    async def update(self, role: Role, update_data: dict) -> Role:
        for key, value in update_data.items():
            setattr(role, key, value)
        await self.db.commit()
        await self.db.refresh(role)
        return await self.get_by_id(role.id)

    async def delete(self, role: Role) -> None:
        await self.db.delete(role)
        await self.db.commit()

    async def list_all(self, skip: int, limit: int):
        result = await self.db.scalars(
            select(Role).options(selectinload(Role.permissions)).offset(skip).limit(limit)
        )
        return result.unique().all()

    async def assign_to_user(self, role_id: int, user_id: uuid.UUID) -> None:
        stmt = insert(user_roles).values(user_id=user_id, role_id=role_id)
        await self.db.execute(stmt)
        await self.db.commit()

    async def remove_from_user(self, role_id: int, user_id: uuid.UUID) -> None:
        stmt = delete(user_roles).where(
            user_roles.c.user_id == user_id, user_roles.c.role_id == role_id
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def user_has_role(self, user_id: uuid.UUID, role_id: int) -> bool:
        return bool(
            await self.db.scalar(
                select(exists().where(
                    user_roles.c.user_id == user_id, user_roles.c.role_id == role_id
                ))
            )
        )

    async def get_permission_by_id(self, permission_id: int) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.id == permission_id))

    async def add_permission(self, role: Role, permission: Permission) -> Role:
        role.permissions.append(permission)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def remove_permission(self, role: Role, permission: Permission) -> Role:
        role.permissions.remove(permission)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    # ------------------------------------------------------------------
    # Grant delegation: which roles/permissions a holder of `role_id` may
    # hand out to other users.
    # ------------------------------------------------------------------

    async def grantable_role_link_exists(self, role_id: int, grantable_role_id: int) -> bool:
        return bool(
            await self.db.scalar(
                select(exists().where(
                    role_grantable_roles.c.role_id == role_id,
                    role_grantable_roles.c.grantable_role_id == grantable_role_id,
                ))
            )
        )

    async def add_grantable_role(self, role_id: int, grantable_role_id: int) -> None:
        stmt = insert(role_grantable_roles).values(
            role_id=role_id, grantable_role_id=grantable_role_id
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def remove_grantable_role(self, role_id: int, grantable_role_id: int) -> None:
        stmt = delete(role_grantable_roles).where(
            role_grantable_roles.c.role_id == role_id,
            role_grantable_roles.c.grantable_role_id == grantable_role_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def grantable_permission_link_exists(self, role_id: int, permission_id: int) -> bool:
        return bool(
            await self.db.scalar(
                select(exists().where(
                    role_grantable_permissions.c.role_id == role_id,
                    role_grantable_permissions.c.permission_id == permission_id,
                ))
            )
        )

    async def add_grantable_permission(self, role_id: int, permission_id: int) -> None:
        stmt = insert(role_grantable_permissions).values(
            role_id=role_id, permission_id=permission_id
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def remove_grantable_permission(self, role_id: int, permission_id: int) -> None:
        stmt = delete(role_grantable_permissions).where(
            role_grantable_permissions.c.role_id == role_id,
            role_grantable_permissions.c.permission_id == permission_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_grantable_role_ids(self, role_ids: list[int]) -> set[int]:
        if not role_ids:
            return set()
        result = await self.db.scalars(
            select(role_grantable_roles.c.grantable_role_id).where(
                role_grantable_roles.c.role_id.in_(role_ids)
            )
        )
        return set(result.all())

    async def get_grantable_permission_ids(self, role_ids: list[int]) -> set[int]:
        if not role_ids:
            return set()
        result = await self.db.scalars(
            select(role_grantable_permissions.c.permission_id).where(
                role_grantable_permissions.c.role_id.in_(role_ids)
            )
        )
        return set(result.all())
