from app.schema.auth import UserRegister, UserResponse
from app.error.custom_exception import UsernameExist,UserMailExist
from app.services.auth.password import get_password_hash
from fastapi import BackgroundTasks
from app.services.verify import utils
from app.repositories.auth.user import UserRepository
from app.settings import Config
import logging
from app.queue.task import send_email_bg
from app.core.logger import LoggedService
logger = logging.getLogger("app")


class RegisterUser(LoggedService):

    def __init__(self,user_repo: UserRepository,bg_task:BackgroundTasks):
        self.user_repo = user_repo
        self.bg_task = bg_task

    def send_mail(self,user_data):
        try:
            token = utils.create_url_safe_token({"email": user_data.email})
            link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
            html = f"""
            <h1>Verify your Email</h1>
            <p>Please click this <a href="{link}">link</a> to verify your email</p>
            """
            send_email_bg.delay(recipients=[user_data.email], subject="verify your mail", body=html)
            logger.info(f"Email sent successfully to {user_data.email}")

        except Exception as e:
            logger.error(f"Failed to send email to {user_data.email}: {str(e)}")



    async def register(self,user_data:UserRegister):
        existing_user_by_username = await self.user_repo.exists_by_username(user_data.username)
        if existing_user_by_username:
            raise UsernameExist(user_data.username)

        existing_user_by_email = await self.user_repo.exists_by_email(user_data.email)
        if existing_user_by_email:
            raise UserMailExist(user_data.email)

        hashed_password = get_password_hash(user_data.password)

        new_user = await self.user_repo.create(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,
        )

        self.send_mail(user_data)

        return {
            "message":"Account Created Successfully! Check mail to verify your Account",
            "user":UserResponse.model_validate(new_user)
        }
