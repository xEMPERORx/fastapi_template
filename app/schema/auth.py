import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.validation import SafeStr, StrongPassword


class UserRegister(BaseModel):
    username: SafeStr = Field(min_length=3, max_length=50)
    email: EmailStr
    password: StrongPassword


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
