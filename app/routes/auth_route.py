"""
Authentication Router Module

This module defines the authentication endpoints for the API, specifically handling
user login operations. It provides a RESTful interface for users to authenticate
and receive access tokens.
"""
from fastapi import APIRouter
from app.controllers.auth_controller import get_token
from app.models.DTO.user_dto import UserLoginDTO, UserDTO
from app.config.config import ROUTES

# Initialize the router with prefix and tags from configuration
# The prefix is loaded from ROUTES['V1_AUTH']
# Tags are used for API documentation grouping in Swagger/OpenAPI
router = APIRouter(prefix=ROUTES['V1_AUTH'], tags=["Authentication"])

@router.post("", response_model=dict)
async def login(user: UserLoginDTO): 
    """
    Authenticate a user and return an access token.
    
    This endpoint accepts user credentials, validates them, and returns an
    authentication token that can be used for subsequent API requests.
    
    Args:
        user (UserLoginDTO): The login credentials containing:
            - username (str): The user's username
            - password (str): The user's password
    
    Returns:
        dict: A dictionary containing the authentication token and related data.
              The exact structure is defined in the TokenDTO.
    
    Raises:
        HTTPException: May raise various HTTP exceptions:
            - 401 Unauthorized: Invalid credentials
            - 403 Forbidden: User is not allowed to access the system
            - 404 Not Found: User does not exist
"""
    u = UserDTO(username=user.username,password=user.password) 
    token_dto = await get_token(u)
    return token_dto.model_dump()