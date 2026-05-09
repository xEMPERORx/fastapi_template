from fastapi import APIRouter,Cookie, Depends, status,Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Optional
from app.core.dependency_factory import (
    get_login_service,
    get_logout_service,
    get_password_reset_service,
    get_refresh_service,
    get_register_service,
    get_reset_password_service,
    get_verify_mail_service,
)
from app.models.db_model import User
from app.schema.auth import UserNewPassword, UserPasswordReset, UserRegister, UserRegisterResponse, UserResponse, TokenResponse, TokenRefreshRequest
from app.services.auth.current_user import get_current_user
from app.services.auth.login import LoginUser
from app.services.auth.logout import LogoutUser
from app.services.auth.refresh import Refresh
from app.services.auth.register import RegisterUser
from app.services.auth.reset_password import ResetPassword
from app.services.verify.mail_verify import VerifyMail
from app.services.verify.password_reset import PasswordReset
from app.core.logger import log_function


router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
@log_function
async def register_user(
    user_data: UserRegister,
    register_service: Annotated[RegisterUser, Depends(get_register_service)],
):
    """
    Register a new user account.
    """
    return await register_service.register(user_data=user_data)

@router.get("/verify/{token}")
@log_function
async def verify_user_account(
    token: str,
    verify_service: Annotated[VerifyMail, Depends(get_verify_mail_service)],
):
    """
    Verify the mail via token
    """
    return await verify_service.verify_mail(token)


@router.post("/login", response_model=TokenResponse)
@log_function
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm,Depends()],
    response:Response,
    login_service: Annotated[LoginUser, Depends(get_login_service)],
):
    """
    Authenticate a user and return a JWT access token.
    """
    return await login_service.login(form_data,response)


@router.post("/logout")
@log_function
async def logout_user(
    response:Response,
    logout_service: Annotated[LogoutUser, Depends(get_logout_service)],
    refresh_token:Optional[str] = Cookie(None, alias="refresh_token"),
):
    """
    Implement the Logout Functionality
    """
    return await logout_service.logout(refresh_token,response)


@router.post("/refresh", response_model=TokenResponse)
@log_function
async def refresh_access_token(
    payload: TokenRefreshRequest,
    refresh_service: Annotated[Refresh, Depends(get_refresh_service)],
):
    """
    Use Refresh Token To get new access Token and refresh Token.
    """
    return await refresh_service.refresh(payload=payload)


@router.post("/reset/password")
@log_function
async def reset_password_mail(
    user_email:UserPasswordReset,
    reset_password_service: Annotated[ResetPassword, Depends(get_reset_password_service)],
):

    return await reset_password_service.reset_password(user_email)


@router.post("/reset/password/{token}/verify")
@log_function
async def reset_password_update(
    token:str,
    user_data:UserNewPassword,
    password_reset_service: Annotated[PasswordReset, Depends(get_password_reset_service)],
):

    return await password_reset_service.verify_password(token,user_data)




@router.get("/user", response_model=UserResponse)
@log_function
async def get_current_user_info(current_user:Annotated[User,Depends(get_current_user)]):
    """Get the currently authenticated user's information."""
    return current_user
