import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.errors.unauthorized_error import UnauthorizedError


security = HTTPBearer()


API_TOKEN = os.getenv("API_TOKEN", "secret-token")




def require_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Dependency: require a valid bearer token. Raises 401 if token invalid."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Invalid auth scheme")
    token = credentials.credentials
    if token != API_TOKEN:
        raise UnauthorizedError("Invalid token")
    return token