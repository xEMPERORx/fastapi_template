from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz_cache import authz_cache
from app.core.logger import log_function
from app.core.rbac.mask import hex_to_mask
from app.core.rbac.principal import Principal
from app.database.postgres_db import get_db
from app.error.auth import InvalidToken, StaleToken, TenantInactive, UserDeactivated, UserNotFound
from app.repositories.auth.user import UserRepository
from app.schema.auth import TokenPayload
from app.services.auth.token import oauth2_scheme, verify_token


def _authenticate(token: str) -> TokenPayload:
    """Decode + validate the bearer token, then fail fast against the
    in-process authz cache (`app.core.authz_cache`) — zero DB/network I/O.
    Shared by `get_current_user` and `get_current_principal` so both paths
    honor a deactivated user/tenant or a stale permission mask identically.
    """
    payload = verify_token(token)
    if payload is None:
        raise InvalidToken()
    if authz_cache.is_user_inactive(payload.id):
        raise UserDeactivated()
    if authz_cache.is_tenant_inactive(payload.tenant_id):
        raise TenantInactive()
    if authz_cache.is_stale(payload.id, payload.perm_version):
        raise StaleToken()
    return payload


@log_function
async def get_current_principal(token: str = Depends(oauth2_scheme)) -> Principal:
    """Fast path for `permission_required`: trusts the JWT's permission mask
    once the cache checks above pass — no DB query at all. Use this instead
    of `get_current_user` for checks that only need `is_superuser`/
    `perm_mask`, not the full `User` object or its `.roles`."""
    payload = _authenticate(token)
    return Principal(
        id=payload.id,
        tenant_id=payload.tenant_id,
        is_superuser=payload.is_superuser,
        perm_mask=hex_to_mask(payload.perm_mask),
        perm_version=payload.perm_version,
    )


@log_function
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Extract and verify the bearer token from the Authorization header,
    then load the full `User` (with `.roles`/`.permissions`) from the DB.
    Needed wherever grant-delegation or role-name checks require the real
    ORM object — see `Principal`'s docstring for why those can't use the
    JWT-only fast path the way `permission_required` does."""
    payload = _authenticate(token)

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_grants(payload.id)
    if user is None:
        raise UserNotFound(payload.id)
    return user
