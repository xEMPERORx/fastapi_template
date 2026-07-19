"""Dependency wiring for the auth/user-account domain: repositories and the
register/login/logout/refresh/reset-password/Google-OAuth service factories.
"""

from typing import Annotated

from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres_db import get_db
from app.repositories.auth.token import RefreshTokenRepository
from app.repositories.auth.user import UserRepository
from app.repositories.tenant.tenant import TenantRepository
from app.services.auth.actions.google_oauth import GoogleOAuthService
from app.services.auth.actions.login import LoginUser
from app.services.auth.actions.logout import LogoutUser
from app.services.auth.actions.refresh import Refresh
from app.services.auth.actions.register import RegisterUser
from app.services.auth.actions.reset_password import ResetPassword
from app.services.verify.mail_verify import VerifyMail
from app.services.verify.password_reset import PasswordReset


def get_tenant_repository_for_auth(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantRepository:
    """Local factory rather than importing `dependency_factory.tenant` — that
    module imports `get_user_repository` from here, so importing it back
    would be circular. Same repository, wired independently on each side."""
    return TenantRepository(db)


def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)


def get_refresh_token_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_register_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    bg_task: BackgroundTasks,
) -> RegisterUser:
    return RegisterUser(user_repo, bg_task)


def get_login_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repository_for_auth)],
) -> LoginUser:
    return LoginUser(user_repo, token_repo, tenant_repo)


def get_logout_service(
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> LogoutUser:
    return LogoutUser(token_repo)


def get_refresh_service(
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repository_for_auth)],
) -> Refresh:
    return Refresh(token_repo, user_repo, tenant_repo)


def get_reset_password_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    bg_task: BackgroundTasks,
) -> ResetPassword:
    return ResetPassword(user_repo, bg_task)


def get_verify_mail_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> VerifyMail:
    return VerifyMail(user_repo)


def get_password_reset_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> PasswordReset:
    return PasswordReset(user_repo)


def get_google_oauth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repository_for_auth)],
) -> GoogleOAuthService:
    return GoogleOAuthService(user_repo, token_repo, tenant_repo)
