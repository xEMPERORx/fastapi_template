import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import LoggedRepository
from app.models.db_model import RefreshToken


class RefreshTokenRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: str, user_id: uuid.UUID, expires_at: datetime) -> RefreshToken:
        db_token = RefreshToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.add(db_token)
        await self.db.commit()
        return db_token

    async def get_by_token(self, token: str) -> RefreshToken | None:
        return await self.db.scalar(select(RefreshToken).where(RefreshToken.token == token))

    async def delete_by_token(self, token: str) -> None:
        await self.db.execute(delete(RefreshToken).where(RefreshToken.token == token))
        await self.db.commit()

    async def delete_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        await self.db.commit()

    async def revoke(self, token_row: RefreshToken) -> None:
        token_row.is_revoked = True
        await self.db.commit()

    async def delete_instance(self, token_row: RefreshToken) -> None:
        await self.db.delete(token_row)
        await self.db.commit()
