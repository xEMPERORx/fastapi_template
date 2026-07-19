from datetime import datetime, timedelta
from typing import Optional
import uuid

import jwt
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core.logger import log_function
from app.core.rbac.mask import mask_to_hex
from app.schema.auth import TokenPayload
from app.settings import Config

SECRET_KEY = Config.SECRET_KEY
REFRESH_SECRET_KEY = Config.REFRESH_KEY
ALGORITHM = Config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_EXPIRE = Config.REFRESH_TOKEN_EXPIRE

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", refreshUrl="/api/v1/auth/refresh")


@log_function
def create_access_token(
    user_id: uuid.UUID,
    tenant_id: Optional[uuid.UUID],
    is_superuser: bool,
    perm_mask: int,
    perm_version: int,
    expires_delta: Optional[timedelta] = None,
    auth_method: str = "password",
) -> str:
    """Create a JWT access token carrying the user's effective permission
    mask + version (see `TokenPayload`), so most requests can authorize
    entirely off the token — no DB query — via the authz cache
    (`app.core.authz_cache`).
    """
    expires = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = TokenPayload(
        id=user_id,
        tenant_id=tenant_id,
        is_superuser=is_superuser,
        perm_mask=mask_to_hex(perm_mask),
        perm_version=perm_version,
        exp=expires,
        auth_method=auth_method,
    )
    # `mode="json"` is needed so `uuid.UUID` fields serialize (PyJWT's own
    # JSON encoder can't handle them), but that also turns `exp` into an ISO
    # string — restore it as a real `datetime` afterward so PyJWT's own
    # special-cased "exp" handling still applies.
    to_encode = payload.model_dump(mode="json", exclude={"exp"})
    to_encode["exp"] = expires
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


@log_function
def create_refresh_token(subject: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a refresh JWT token with an expiration time.

    Includes a random `jti` so two logins for the same user within the same
    second don't produce byte-identical tokens — `exp` has 1-second
    resolution, and without a nonce a same-second double-login collides on
    `refreshtoken.token`'s primary key.
    """
    expires = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode = {"exp": expires, "user": subject, "jti": uuid.uuid4().hex}
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, ALGORITHM)


@log_function
def verify_token(token: str) -> Optional[TokenPayload]:
    """Verify and decode a JWT access token, returning its typed claims."""
    try:
        raw = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM] if ALGORITHM else ["HS256"])
        return TokenPayload.model_validate(raw)
    except (jwt.PyJWTError, ValidationError):
        return None


@log_function
def verify_refresh_token(token: str):
    """Verify and decode a JWT refresh token."""
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM] if ALGORITHM else ["HS256"])
        user = payload.get("user")
        if user["id"] is None:
            return None
        return uuid.UUID(user["id"])
    except jwt.PyJWTError:
        return None
