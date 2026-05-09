from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
import uuid


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class UserRegisterResponse(BaseModel):
    message: str
    user: UserResponse

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class UserPasswordReset(BaseModel):
    email: EmailStr


class UserNewPassword(BaseModel):
    new_password: str
    confirm_password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class GoogleAuthUrlResponse(BaseModel):
    authorization_url: str
    state: str


class GoogleOAuthCallbackResponse(TokenResponse):
    user: UserResponse
    is_new_user: bool
