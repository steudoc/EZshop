from app.models.DAO.user_dao import UserDAO
from app.models.DTO.user_dto import UserDTO
from app.models.DTO.token_dto import TokenDTO
from app.models.DTO.error_dto import ErrorDTO
from app.models.DAO.system_dao import SystemInfoDAO
from app.models.DTO.system_dto import SystemInfoDTO, SystemInfoResponseDTO


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

def systemdao_to_dto(system_info_dao: SystemInfoDAO) -> SystemInfoDTO:
    return SystemInfoDTO(
        id=system_info_dao.id,
        balance=system_info_dao.balance
    )

def systemdao_to_responsedto(system_info_dao: SystemInfoDAO) -> SystemInfoResponseDTO:
    return SystemInfoResponseDTO(
        balance=system_info_dao.balance
    )