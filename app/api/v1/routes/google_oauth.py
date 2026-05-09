from typing import Annotated
from fastapi import APIRouter, Depends, Request

from app.core.dependency_factory import get_google_oauth_service
from app.core.logger import log_function
from app.schema.auth import GoogleOAuthCallbackResponse
from app.services.auth.google_oauth import GoogleOAuthService


router = APIRouter(tags=["Auth"])


@router.get("/google")
@log_function
async def auth_google(
    request: Request,
    oauth_service: Annotated[GoogleOAuthService, Depends(get_google_oauth_service)],
):
    return await oauth_service.authorize_redirect(request)


@router.get("/google/callback", response_model=GoogleOAuthCallbackResponse)
@log_function
async def google_callback(
    request: Request,
    oauth_service: Annotated[GoogleOAuthService, Depends(get_google_oauth_service)],
):
    return await oauth_service.handle_callback(request)
