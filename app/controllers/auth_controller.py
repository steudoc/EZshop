from fastapi import HTTPException, status
from app.models.DTO.user_dto import UserDTO
from app.models.DTO.token_dto import TokenDTO
from app.repositories.user_repository import UserRepository
from app.services.auth_service import generate_token
from app.services.mapper_service import create_token_dto, userdao_to_dto
from app.models.errors.unauthorized_error import UnauthorizedError
from app.models.errors.notfound_error import NotFoundError


async def get_token(user_dto: UserDTO) -> TokenDTO:
    user_repo = UserRepository()
    try:
        user_dao = await user_repo.get_user_by_username(user_dto.username)
    except NotFoundError:
    #if not user_dao:
        raise NotFoundError("Entity not found")

    if user_dto.password != user_dao.password:
        raise UnauthorizedError("Invalid password")

    token_str = generate_token(userdao_to_dto(user_dao))
    return create_token_dto(token_str)
