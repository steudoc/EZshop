from app.models.DAO.user_dao import UserDAO
from app.models.DAO.product_dao import ProductDAO
from app.models.DTO.user_dto import UserDTO
from app.models.DTO.product_dto import ProductDTO
from app.models.DTO.token_dto import TokenDTO
from app.models.DTO.error_dto import ErrorDTO
from app.models.DTO.return_dto import ReturnDTO
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
def systemdao_to_dto(system_info_dao: SystemInfoDAO) -> SystemInfoDTO:
    return SystemInfoDTO(
        id=system_info_dao.id,
        balance=system_info_dao.balance
    )

def systemdao_to_responsedto(system_info_dao: SystemInfoDAO) -> SystemInfoResponseDTO:
    return SystemInfoResponseDTO(
        balance=system_info_dao.balance
    )

def productdao_to_dto(product_dao: ProductDAO) -> ProductDTO:
    return ProductDTO(
        id=product_dao.id,
        description=product_dao.description,
        barcode=product_dao.barcode,
        price_per_unit=product_dao.price_per_unit,
        note=product_dao.note,
        quantity=product_dao.quantity,
        position=product_dao.position
    )

def update_productdao_from_partial_dto(product_dao: ProductDAO, product_dto: ProductDTO) -> None:
    if (product_dto.barcode is not None):
        product_dao.barcode = product_dto.barcode

    if (product_dto.description is not None):
        product_dao.description = product_dto.description

    if (product_dto.price_per_unit is not None):
        product_dao.price_per_unit = product_dto.price_per_unit

    if (product_dto.note is not None):
        product_dao.note = product_dto.note
        
    if (product_dto.position is not None):
        product_dao.position = product_dto.position
        
    if (product_dto.quantity is not None):
        product_dao.quantity = product_dto.quantity
