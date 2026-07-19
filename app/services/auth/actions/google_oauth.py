from datetime import datetime, timedelta

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request, status

from app.core.security.validation import sanitize_identifier
from app.repositories.auth.token import RefreshTokenRepository
from app.repositories.auth.user import UserRepository
from app.repositories.tenant.tenant import TenantRepository
from app.schema.auth import GoogleOAuthCallbackResponse, UserResponse
from app.services.auth.mint import mint_access_token
from app.services.auth.token import create_refresh_token
from app.settings import Config
from app.core.logger import LoggedService


oauth = OAuth()
oauth.register(
	name="google",
	client_id=Config.GOOGLE_CLIENT_ID,
	client_secret=Config.GOOGLE_CLIENT_SECRET,
	server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
	authorize_params={
		"scope": Config.GOOGLE_SCOPE,
		"access_type": Config.GOOGLE_ACCESS_TYPE,
		"prompt": Config.GOOGLE_PROMPT,
	},
	client_kwargs={"scope": Config.GOOGLE_SCOPE},
)



class GoogleOAuthService(LoggedService):
	def __init__(self, user_repo: UserRepository, token_repo: RefreshTokenRepository, tenant_repo: TenantRepository):
		self.user_repo = user_repo
		self.token_repo = token_repo
		self.tenant_repo = tenant_repo

	async def authorize_redirect(self, request: Request):
		if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail="Google OAuth is not configured",
			)
		return await oauth.google.authorize_redirect(request, Config.GOOGLE_REDIRECT_URI)

	async def handle_callback(self, request: Request) -> GoogleOAuthCallbackResponse:
		token = await oauth.google.authorize_access_token(request)
		user_info = token.get("userinfo") or {}
		email = user_info.get("email")

		if not email:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Email not provided by Google",
			)

		user = await self.user_repo.get_by_email(email)
		is_new_user = False

		if not user:
			username = await self._build_unique_username(email)
			user = await self.user_repo.create(
				username=username,
				email=email,
				password=None,
				is_verified=True,
			)
			is_new_user = True

		user_with_grants = await self.user_repo.get_by_id_with_grants(user.id)
		access_token = await mint_access_token(user_with_grants, self.tenant_repo, auth_method="google")
		refresh_expiry = datetime.utcnow() + timedelta(days=Config.REFRESH_TOKEN_EXPIRE)
		refresh_token = create_refresh_token(
			subject={"id": str(user.id)},
			expires_delta=timedelta(days=Config.REFRESH_TOKEN_EXPIRE),
		)

		await self.token_repo.create(
			token=refresh_token,
			user_id=user.id,
			expires_at=refresh_expiry,
		)

		return GoogleOAuthCallbackResponse(
			access_token=access_token,
			refresh_token=refresh_token,
			token_type="bearer",
			user=UserResponse.model_validate(user),
			is_new_user=is_new_user,
		)

	async def _build_unique_username(self, email: str) -> str:
		base_username = sanitize_identifier(email.split("@")[0])
		candidate = base_username
		suffix = 1

		while await self.user_repo.exists_by_username(candidate):
			suffix += 1
			candidate = f"{base_username}{suffix}"

		return candidate
