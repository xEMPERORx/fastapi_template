from fastapi import Response
from app.core.logger import LoggedService
from app.repositories.auth.token import RefreshTokenRepository

class LogoutUser(LoggedService):
    def __init__(self, token_repo: RefreshTokenRepository):
        self.token_repo = token_repo

    async def logout(self, refresh_token: str, response: Response):

        if refresh_token:
            await self.token_repo.delete_by_token(refresh_token)

        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="lax"
        )

        return {"message": "Successfully logged out"}
