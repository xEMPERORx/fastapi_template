from app.error.auth import UserNotFound
from app.schema.auth import UserNewPassword
from app.services.auth.password import get_password_hash
from app.services.verify.utils import decode_password_reset_token
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status
from app.repositories.auth.user import UserRepository
from app.core.logger import LoggedService


class PasswordReset(LoggedService):

    def __init__(self,user_repo: UserRepository):
         self.user_repo = user_repo

    async def verify_password(self,token:str,user_data:UserNewPassword):
        token_data = decode_password_reset_token(token)
        user_email = token_data.get("email")

        if user_email:
            user = await self.user_repo.get_by_email(user_email)

            if not user:
                raise UserNotFound()

            if user_data.new_password != user_data.confirm_password:
                raise HTTPException(status_code=404,detail="Password and confirm Password are not same")


            hashed_password = get_password_hash(user_data.new_password)

            await self.user_repo.set_password(user, hashed_password)

            return JSONResponse(
                content={"message": "Account Password Reset Successfully"},
                status_code=status.HTTP_200_OK,
            )

        return JSONResponse(
            content={"message": "Error occured during Reset Password"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
