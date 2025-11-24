from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.DTO.user_dto import UserDTO, UserCreateDTO, UserResponseDTO
from app.models.user_type import UserType
from app.controllers.user_controller import UserController
from app.middleware.auth_middleware import authenticate_user
from app.config.config import ROUTES
from fastapi import Response
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError


router = APIRouter(prefix=ROUTES['V1_USERS'], tags=["Users"])
controller = UserController()

@router.post("/", 
    response_model=UserResponseDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def create_user(user: UserCreateDTO):
    """
    Create a new user.

    - Permissions: Administrator
    - Request body: UserCreateDTO (contains username, password, type, ...)
    - Returns: Created user as UserResponseDTO
    - Raises:
      - BadRequestError: when mandatory fields (password, type) are missing or invalid
    - Status code: 201 Created
    """
    if user.password is None or user.password == '':
        raise BadRequestError('Password is a mandatory field')
    if user.type is None or user.type == '':
        raise BadRequestError('User type is a mandatory field')
    return await controller.create_user(user)
    
@router.get("/", response_model=List[UserResponseDTO],
            dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def list_users():
    """
    List all users.

    - Permissions: Administrator
    - Returns: List of UserResponseDTO
    - Status code: 200 OK
    """
    return await controller.list_users()


@router.get("/{user_id}", response_model=UserResponseDTO,
            dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def get_user(user_id: int):
    """
    Retrieve a single user by ID.

    - Permissions: Administrator
    - Path parameter: user_id (int)
    - Returns: UserResponseDTO for the requested user
    - Raises:
      - NotFoundError: when the user does not exist
    - Status code: 200 OK
    """
    user = await controller.get_user(user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


@router.put("/{user_id}", response_model=UserResponseDTO, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def update_user(user_id: int, user: UserDTO):
    """
    Update an existing user.

    - Permissions: Administrator
    - Path parameter: user_id (int)
    - Request body: UserDTO (fields to update)
    - Returns: Updated user as UserResponseDTO
    - Raises:
      - NotFoundError: when the user to update does not exist
    - Status code: 201 Created
    """
    updated = await controller.update_user(user_id, user)
    if not updated:
        raise NotFoundError("User not found")
    return updated


@router.delete("/{user_id}", 
               status_code=status.HTTP_204_NO_CONTENT, 
               dependencies=[Depends(authenticate_user([UserType.Administrator]))])
async def delete_user(user_id: int):
    """
    Delete a user by ID.

    - Permissions: Administrator
    - Path parameter: user_id (int)
    - Returns: No content (204) on success
    - Raises:
      - NotFoundError: when the user to delete does not exist
    - Status code: 204 No Content
    """
    success = await controller.delete_user(user_id)
    if not success:
        raise NotFoundError("User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)