from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Response
from app.schema.auth import TokenResponse
from app.core.rate_limiters import login_limiter
from app.error.custom_exception import RateLimit, UserNotVerified, UserUnauthenticated
from app.services.auth.password import verify_password
from app.services.auth.token import create_access_token, create_refresh_token
from app.settings import Config
from app.repositories.auth.user import UserRepository
from app.repositories.auth.token import RefreshTokenRepository
import os
ENV = os.getenv("ENV", "development")

REFRESH_EXPIRE = Config.REFRESH_TOKEN_EXPIRE

from app.core.logger import LoggedService


class LoginUser(LoggedService):

    def __init__(self, user_repo: UserRepository, token_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def login(self,form_data:OAuth2PasswordRequestForm,response:Response):

        if not await login_limiter.is_allowed(form_data.username):
            raise RateLimit(
                message="Too many login attempts for this account. Please wait before trying again.",
                headers={"Retry-After": str(login_limiter.window)},
            )

        user = await self.user_repo.get_by_username(form_data.username)


        if not user or not verify_password(form_data.password, user.password):
            raise UserUnauthenticated()

        if user.is_verified == False:
            raise UserNotVerified()

        access_token = create_access_token({"id":str(user.id)})
        refresh_token = create_refresh_token({"id":str(user.id)})
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True if ENV == "production" else False,
            samesite="lax",
            max_age=REFRESH_EXPIRE * 24 * 60 * 60,
        )

        await self.token_repo.create(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow()+timedelta(days=REFRESH_EXPIRE),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
