import uuid
from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import LoggedRepository
from app.models.db_model import User


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
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password=password,
            is_verified=is_verified,
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

    async def set_verified(self, user: User) -> None:
        user.is_verified = True
        await self.db.commit()

    async def set_password(self, user: User, hashed_password: str) -> None:
        user.password = hashed_password
        await self.db.commit()
