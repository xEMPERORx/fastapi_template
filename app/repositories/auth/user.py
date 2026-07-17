import uuid
from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logger import LoggedRepository
from app.models.db_model import Permission, Role, User


class UserRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def exists_by_username(self, username: str) -> bool:
        return bool(
            await self.db.scalar(select(exists().where(User.username == username)))
        )

    async def exists_by_email(self, email: str) -> bool:
        return bool(await self.db.scalar(select(exists().where(User.email == email))))

    async def create(
        self,
        username: str,
        email: str,
        password: Optional[str],
        is_verified: bool = False,
        is_superuser: bool = False,
        created_by_id: Optional[uuid.UUID] = None,
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password=password,
            is_verified=is_verified,
            is_superuser=is_superuser,
            created_by_id=created_by_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_username(self, username: str) -> User | None:
        return await self.db.scalar(select(User).where(User.username == username))

    async def get_by_email(self, email: str) -> User | None:
        return await self.db.scalar(select(User).where(User.email == email))

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.scalar(select(User).where(User.id == user_id))

    async def get_by_id_with_grants(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user with roles, role permissions, and direct permissions eagerly loaded."""
        return await self.db.scalar(
            select(User)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.permissions),
            )
            .where(User.id == user_id)
        )

    async def list_all(self, skip: int, limit: int) -> list[User]:
        result = await self.db.scalars(
            select(User)
            .options(selectinload(User.roles))
            .offset(skip)
            .limit(limit)
            .order_by(User.username)
        )
        return result.unique().all()

    async def count_all(self) -> int:
        return await self.db.scalar(select(func.count()).select_from(User)) or 0

    async def set_verified(self, user: User) -> None:
        user.is_verified = True
        await self.db.commit()

    async def set_password(self, user: User, hashed_password: str) -> None:
        user.password = hashed_password
        await self.db.commit()

    async def has_permission(self, user_id: uuid.UUID, permission_id: int) -> bool:
        from app.models.db_model import user_permissions

        return bool(
            await self.db.scalar(
                select(exists().where(
                    user_permissions.c.user_id == user_id,
                    user_permissions.c.permission_id == permission_id,
                ))
            )
        )

    async def grant_permission(self, user: User, permission: Permission) -> None:
        user.permissions.append(permission)
        await self.db.commit()

    async def revoke_permission(self, user: User, permission: Permission) -> None:
        user.permissions.remove(permission)
        await self.db.commit()
