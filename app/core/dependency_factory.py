from typing import Annotated
from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from app.database.db import get_db
from app.database.redis_db import redis_connect
from app.repositories.auth.token import RefreshTokenRepository
from app.repositories.auth.user import UserRepository
from app.repositories.rbac.permission import PermissionRepository
from app.repositories.rbac.role import RoleRepository
from app.repositories.search.search import SearchRepository
from app.services.auth.login import LoginUser
from app.services.auth.logout import LogoutUser
from app.services.auth.refresh import Refresh
from app.services.auth.register import RegisterUser
from app.services.auth.reset_password import ResetPassword
from app.services.auth.google_oauth import GoogleOAuthService
from app.services.permission.service import PermissionService
from app.services.roles.service import RoleService
from app.services.search.service import SearchService
from app.services.users.service import UserManagementService
from app.services.verify.mail_verify import VerifyMail
from app.services.verify.password_reset import PasswordReset
from app.core.esclient import get_es_client
from elasticsearch import AsyncElasticsearch


def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)

def get_refresh_token_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)

def get_role_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleRepository:
    return RoleRepository(db)

def get_permission_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PermissionRepository:
    return PermissionRepository(db)


def get_search_repository(
    es_client: Annotated[AsyncElasticsearch, Depends(get_es_client)],
) -> SearchRepository:
    return SearchRepository(es_client)

def get_search_service(
    repo: Annotated[SearchRepository, Depends(get_search_repository)],
) -> SearchService:
    return SearchService(repo)

def get_role_service(
    repo: Annotated[RoleRepository, Depends(get_role_repository)],
    permission_repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
) -> RoleService:
    return RoleService(repo, permission_repo)


def get_permission_service(
    repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
) -> PermissionService:
    return PermissionService(repo)


def get_register_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    bg_task: BackgroundTasks,
) -> RegisterUser:
    return RegisterUser(user_repo, bg_task)


def get_login_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> LoginUser:
    return LoginUser(user_repo, token_repo)


def get_logout_service(
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> LogoutUser:
    return LogoutUser(token_repo)


def get_refresh_service(
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> Refresh:
    return Refresh(token_repo)


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
) -> GoogleOAuthService:
    return GoogleOAuthService(user_repo, token_repo)


def get_user_management_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repository)],
    permission_repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
) -> UserManagementService:
    return UserManagementService(user_repo, role_repo, permission_repo)
