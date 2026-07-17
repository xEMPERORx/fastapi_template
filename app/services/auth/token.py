from datetime import datetime, timedelta
from typing import Optional
import uuid

import jwt
from fastapi.security import OAuth2PasswordBearer

from app.core.logger import log_function
from app.settings import Config

SECRET_KEY = Config.SECRET_KEY
REFRESH_SECRET_KEY = Config.REFRESH_KEY
ALGORITHM = Config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_EXPIRE = Config.REFRESH_TOKEN_EXPIRE

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", refreshUrl="/api/v1/auth/refresh")


@log_function
def create_access_token(subject: dict, expires_delta: Optional[timedelta] = None, auth_method: str = "password") -> str:
    """Create a JWT access token with an expiration time."""
    to_encode = subject.copy()
    expires = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expires, "auth_method": auth_method})
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
def verify_token(token: str):
    """Verify and decode a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM] if ALGORITHM else ["HS256"])
        user = payload.get("id")
        if user is None:
            return None
        return uuid.UUID(user)
    except jwt.PyJWTError:
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
