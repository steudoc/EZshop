from sqlalchemy.ext.asyncio import AsyncSession
from app.models.DAO.user_dao import UserDAO
from app.models.DAO.product_dao import ProductDAO
from app.models.DTO.user_dto import UserDTO
from app.models.DAO.card_dao import CardDAO
from app.models.DAO.customer_dao import CustomerDAO
from app.models.DAO.system_dao import SystemInfoDAO
from app.models.DAO.order_dao import OrderDAO
from app.models.DTO.sale_dto import SaleDTO, SaleLineDTO
from app.models.DAO.sale_dao import SaleDAO
from app.models.DTO.product_dto import ProductDTO
from app.models.DTO.token_dto import TokenDTO
from app.models.DTO.error_dto import ErrorDTO
from app.models.DTO.return_dto import ReturnDTO, ReturnLineDTO
from app.models.DTO.order_dto import OrderDTO
from app.models.DTO.system_dto import SystemInfoDTO, SystemInfoResponseDTO
from app.models.DTO.customer_dto import CustomerDTO, CardDTO
from app.repositories.card_repository import CardRepository

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
    lines = []
    for line_dao in return_dao.lines:
        lines.append(ReturnLineDTO(
            id=line_dao.id,
            return_id=line_dao.return_id,
            product_barcode=line_dao.product_barcode,
            quantity=line_dao.quantity,
            price_per_unit=line_dao.price_per_unit
        ))
    return ReturnDTO(
        id=return_dao.id,
        sale_id=return_dao.sale_id,
        status=return_dao.status,
        created_at=return_dao.created_at,
        closed_at=return_dao.closed_at,
        lines=lines
    )

def orderdao_to_dto(order_dao: OrderDAO) -> OrderDTO:
    return OrderDTO(
        id=order_dao.id,
        product_barcode=order_dao.product_barcode,
        quantity=order_dao.quantity,
        price_per_unit=order_dao.price_per_unit,
        status=order_dao.status,
        issue_date=order_dao.issue_date
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


def carddao_to_response_dto(card_dao: CardDAO) -> CardDTO:
    return CardDTO(
        card_id = card_dao.cardId,
        points = card_dao.points
    )

def customerdao_and_card_to_dto(customer: CustomerDAO, card: CardDAO | None = None) -> CustomerDTO:
        return CustomerDTO(
            id=customer.id,
            name=customer.name,
            card=(
                CardDTO(
                    card_id=card.cardId,
                    points=card.points
                )
                if card is not None
                else None
            )
        )


async def customerdao_to_responsedto(customer_dao: CustomerDAO) -> CustomerDTO:
    # Nota: Istanziare un repository dentro un mapper non è ideale (rischio circular import),
    # ma se viene da develop lo manteniamo così per ora.
    card_repository = CardRepository()
    card_dao = await card_repository.get_card_by_customer_without_raise_notfounderror(customer_dao.id)
    card_dto = carddao_to_response_dto(card_dao) if card_dao else None
    
    return CustomerDTO(
        id=customer_dao.id,
        name=customer_dao.name,
        card=card_dto
    )

def sale_dao_to_dto(sale_dao) -> SaleDTO:
    if not sale_dao:
        return None
    
    sale_dto = SaleDTO(
        id=sale_dao.id,
        created_at=sale_dao.created_at,
        closed_at=sale_dao.closed_at,
        status=sale_dao.status,
        discount_rate=sale_dao.discount_rate,
        lines=[
            SaleLineDTO(
                id=line.id,
                sale_id=line.sale_id,
                product_barcode=line.product_barcode,
                quantity=line.quantity,
                price_per_unit=line.price_per_unit,
                discount_rate=line.discount_rate
            ) for line in sale_dao.lines
        ]
    )
    return sale_dto
