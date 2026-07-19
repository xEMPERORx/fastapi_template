from itsdangerous import URLSafeTimedSerializer
from app.settings import Config
from fastapi import HTTPException


serializer = URLSafeTimedSerializer(
    secret_key=Config.SECRET_KEY, salt="email-configuration"
)

# Separate salt (and much shorter expiry) from the email-verification
# serializer above: a password-reset link grants an account takeover if
# it leaks, so it shouldn't stay valid for a full day like a verification
# link does. Self-contained/stateless by design — no Redis-backed lookup
# needed since itsdangerous encodes the expiry into the signed token itself.
password_reset_serializer = URLSafeTimedSerializer(
    secret_key=Config.SECRET_KEY, salt="password-reset"
)
PASSWORD_RESET_MAX_AGE_SECONDS = 60 * 30


def create_url_safe_token(data: dict):

    token = serializer.dumps(data)

    return token

def decode_url_safe_token(token:str):
    try:
        token_data = serializer.loads(token, max_age=60 * 60 * 24)

        return token_data

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")


def create_password_reset_token(data: dict) -> str:
    return password_reset_serializer.dumps(data)


def decode_password_reset_token(token: str) -> dict:
    try:
        return password_reset_serializer.loads(token, max_age=PASSWORD_RESET_MAX_AGE_SECONDS)
    except Exception:
        raise HTTPException(status_code=400, detail="Link expired or already used")
