from app.error.custom_exception import UserNotFound
from app.services.verify.utils import decode_url_safe_token
from fastapi.responses import JSONResponse
from fastapi import status
from app.repositories.auth.user import UserRepository
from app.core.logger import LoggedService

class VerifyMail(LoggedService):

    def __init__(self,user_repo: UserRepository):
         self.user_repo = user_repo

    async def verify_mail(self,token:str):
        token_data = decode_url_safe_token(token)
        user_email = token_data.get("email")

        if user_email:
            user = await self.user_repo.get_by_email(user_email)

            if not user:
                raise UserNotFound()

            await self.user_repo.set_verified(user)

            return JSONResponse(
                content={"message": "Account verified successfully"},
                status_code=status.HTTP_200_OK,
            )

        return JSONResponse(
            content={"message": "Error occured during verification"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
