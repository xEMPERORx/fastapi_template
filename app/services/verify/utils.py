from itsdangerous import URLSafeTimedSerializer
from app.settings import Config
from fastapi import HTTPException


serializer = URLSafeTimedSerializer(
    secret_key=Config.SECRET_KEY, salt="email-configuration"
)


def create_url_safe_token(data: dict):

    token = serializer.dumps(data)

    return token

def decode_url_safe_token(token:str):
    try:
        token_data = serializer.loads(token, max_age=60 * 60 * 24)

        return token_data

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
