import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


API_TOKEN = os.getenv("API_TOKEN", "secret-token")




def require_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Dependency: require a valid bearer token. Raises 401 if token invalid."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    token = credentials.credentials
    if token != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token