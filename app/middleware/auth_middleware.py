
from fastapi import  HTTPException, Header, status
from typing import Optional, List
from app.services.auth_service import process_token
from app.models.user_type import UserType
from app.models.errors.unauthorized_error import UnauthorizedError

# Factory: returns an async dependency callable
def authenticate_user(allowed_roles: List[UserType]):
    async def _dep(authorization: Optional[str] = Header(None, alias="Authorization")):
        if authorization is None:
            raise UnauthorizedError(message="Authorization header missing")
        # process_token should raise if the role isn't allowed
        return await process_token(authorization, allowed_roles)
    return _dep