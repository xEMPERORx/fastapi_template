from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_URL: str
    SECRET_KEY: str
    REFRESH_KEY:str
    ACCESS_TOKEN_EXPIRE_MINUTES :int
    REFRESH_TOKEN_EXPIRE :int
    ALGORITHM: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    DOMAIN: str
    REDIS_HOST :str
    REDIS_PORT:int
    REDIS_URL :str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_SCOPE: str
    GOOGLE_ACCESS_TYPE: str
    GOOGLE_PROMPT: str
    GOOGLE_AUTH_URI: str
    GOOGLE_TOKEN_URI: str
    GOOGLE_USERINFO_URI: str
    beat_dburi :str
    SESSION_SECRET: str
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"])
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


Config = Settings()

broker_url = Config.REDIS_URL
result_backend = f"db+{Config.DB_URL}"

broker_connection_retry_on_startup = True
