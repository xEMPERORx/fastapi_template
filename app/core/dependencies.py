from typing import List
from fastapi import Depends, HTTPException, status
from app.models.db_model import User
from app.services.auth.current_user import get_current_user

def role_required(roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if not any(role.name in roles for role in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker


def permission_required(required_permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)):
        user_permissions = {
            perm.name
            for role in current_user.roles
            for perm in role.permissions
        }
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_permission}"
            )

        return current_user
    return permission_checker
