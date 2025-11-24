
from fastapi import  HTTPException, Header, status
from typing import Optional, List
from app.services.auth_service import process_token
from app.models.user_type import UserType

# Factory: returns an async dependency callable
def authenticate_user(allowed_roles: List[UserType]):
    async def _dep(authorization: Optional[str] = Header(None, alias="Authorization")):
        if authorization is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        # process_token should raise if the role isn't allowed
        return await process_token(authorization, allowed_roles)
    return _dep