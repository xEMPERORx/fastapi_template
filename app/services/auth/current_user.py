from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.error.custom_exception import InvalidToken, UserNotFound
from app.repositories.auth.user import UserRepository
from app.services.auth.token import oauth2_scheme, verify_token
from app.core.logger import log_function


@log_function
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Extract and verify the bearer token from the Authorization header."""
    user_id = verify_token(token)
    if user_id is None:
        raise InvalidToken()

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_grants(user_id)
    if user is None:
        raise UserNotFound(user_id)
    return user
