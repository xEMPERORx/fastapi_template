from app.core.rbac.delegation import effective_permission_mask
from app.core.logger import log_function
from app.error.auth import TenantInactive, UserDeactivated
from app.models.db_model import User
from app.repositories.tenant.tenant import TenantRepository
from app.services.auth.token import create_access_token


@log_function
async def mint_access_token(user: User, tenant_repo: TenantRepository, auth_method: str = "password") -> str:
    """Shared by login/refresh/Google-OAuth: validates the user/tenant are
    still active and mints an access token carrying their effective
    permission mask + `perm_version` (see `TokenPayload`).

    Requires `user.roles`/`user.permissions` already eagerly loaded (see
    `UserRepository.get_by_id_with_grants`) so `effective_permission_mask`
    doesn't trigger lazy-load queries.
    """
    if not user.is_active:
        raise UserDeactivated()

    if user.tenant_id is not None:
        tenant = await tenant_repo.get_by_id(user.tenant_id)
        if tenant is None or not tenant.is_active:
            raise TenantInactive()

    perm_mask = effective_permission_mask(user)
    return create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        is_superuser=user.is_superuser,
        perm_mask=perm_mask,
        perm_version=user.perm_version,
        auth_method=auth_method,
    )
