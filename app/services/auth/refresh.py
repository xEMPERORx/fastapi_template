from app.schema.auth import TokenResponse, TokenRefreshRequest
from app.repositories.auth.token import RefreshTokenRepository
from app.services.auth.token import create_access_token, create_refresh_token
from fastapi import HTTPException
from datetime import datetime, timedelta
from app.settings import Config
from app.core.logger import LoggedService

REFRESH_EXPIRE = Config.REFRESH_TOKEN_EXPIRE

class Refresh(LoggedService):

    def __init__(self, token_repo: RefreshTokenRepository):
        self.token_repo = token_repo


    async def refresh(self, payload: TokenRefreshRequest):

        db_token = await self.token_repo.get_by_token(payload.refresh_token)

        if not db_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if db_token.is_revoked:
            await self.token_repo.delete_all_for_user(db_token.user_id)
            raise HTTPException(
                status_code=403,
                detail="Security breach detected. All sessions invalidated. Please login again."
            )

        if db_token.expires_at < datetime.utcnow():
            await self.token_repo.delete_instance(db_token)
            raise HTTPException(status_code=401, detail="Refresh token expired")

        await self.token_repo.revoke(db_token)
        user_id = db_token.user_id

        new_access_token = create_access_token({"id": str(user_id)})
        new_refresh_token = create_refresh_token({"id": str(user_id)})

        await self.token_repo.create(
            token=new_refresh_token,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_EXPIRE),
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
