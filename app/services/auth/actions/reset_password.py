from app.schema.auth import UserPasswordReset
from app.error.auth import UserNotFound
from fastapi import BackgroundTasks
from app.services.verify import mail_config, utils
from app.settings import Config
import logging
from app.repositories.auth.user import UserRepository
from app.core.logger import LoggedService

logger = logging.getLogger("app")


class ResetPassword(LoggedService):

    def __init__(self,user_repo: UserRepository,bg_task:BackgroundTasks):
        self.user_repo = user_repo
        self.bg_task = bg_task

    async def send_mail(self,user_data):
        try:
            token = utils.create_password_reset_token({"email": user_data.email})

            link = f"http://{Config.DOMAIN}/api/v1/auth/reset/password/{token}/verify"
            html = f"""
            <h1>Reset Password</h1>
            <p>Please click this <a href="{link}">link</a> to Reset the password</p>
            """
            message = mail_config.create_message(
                recipients=[user_data.email], subject="Reset Password", body=html
            )

            await  mail_config.mail.send_message(message)

            logger.info(f"Email sent successfully to {user_data.email}")

        except Exception as e:
            logger.error(f"Failed to send email to {user_data.email}: {str(e)}")



    async def reset_password(self,user_mail:UserPasswordReset):

        existing_user_by_email = await self.user_repo.exists_by_email(user_mail.email)
        if not existing_user_by_email:
            raise UserNotFound(user_mail.email)

        self.bg_task.add_task(self.send_mail,user_mail)

        return {
            "message":"Please Check you mail for password reset link",
        }
