from app.error.custom_exception import InvalidToken

from app.services.auth.token import verify_refresh_token, verify_token
from app.core.logger import LoggedService



class Verify(LoggedService):


    def verify_access(self,token:str):
        user_id = verify_token(token)

        if user_id is None:
            raise InvalidToken()

        return {"message": "Token is valid", "id": user_id}


    def verify_refresh(self,token:str):
        user_id = verify_refresh_token(token)

        if user_id is None:
            raise InvalidToken()

        return {"message": "Token is valid", "id": user_id}
