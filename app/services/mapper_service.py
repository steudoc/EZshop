from app.models.DAO.user_dao import UserDAO
from app.models.DTO.user_dto import UserDTO
from app.models.DTO.token_dto import TokenDTO
from app.models.DTO.error_dto import ErrorDTO
from app.models.DTO.return_dto import ReturnDTO


def create_error_dto(code: int, message: str, name: str) -> ErrorDTO:
    """Create an ErrorDTO instance"""
    return ErrorDTO(code=code, message=message, name=name)

def create_token_dto(token: str) -> TokenDTO:
    return TokenDTO(token=token)

def userdao_to_dto(user_dao: UserDAO) -> UserDTO:
    return UserDTO(
        id=user_dao.id,
        username=user_dao.username,
        password=user_dao.password,
        type=user_dao.type
    )

def userdao_to_responsedto(user_dao: UserDAO) -> UserDTO:
    return UserDTO(
        id=user_dao.id,
        username=user_dao.username,
        type=user_dao.type
    )

def returndao_to_dto(return_dao) -> ReturnDTO:
    return ReturnDTO(
        id=return_dao.id,
        sale_id=return_dao.sale_id,
        status=return_dao.status,
        created_at=return_dao.created_at
    )

def returndao_to_responsedto(return_dao) -> ReturnDTO:
    return ReturnDTO(
        id=return_dao.id,
        sale_id=return_dao.sale_id,
        status=return_dao.status,
        created_at=return_dao.created_at,
        closed_at=return_dao.closed_at
    )