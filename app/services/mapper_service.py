from sqlalchemy.ext.asyncio import AsyncSession
from app.models.DAO.user_dao import UserDAO
from app.models.DAO.card_dao import CardDAO
from app.models.DAO.customer_dao import CustomerDAO

from app.models.DTO.user_dto import UserDTO
from app.models.DTO.token_dto import TokenDTO
from app.models.DTO.error_dto import ErrorDTO
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

def carddao_to_response_dto(card_dao: CardDAO) -> CardDTO:
    return CardDTO(
        cardId = card_dao.cardId,
        points = card_dao.points
    )


async def customerdao_to_responsedto(customer_dao: CustomerDAO) -> CustomerDTO:
    card_repository = CardRepository()
    card_dao = await card_repository.get_card_by_customer(customer_dao.id)
    card_dto = carddao_to_response_dto(card_dao) if card_dao else None
    
    return CustomerDTO(
        id=customer_dao.id,
        name=customer_dao.name,
        card=card_dto
    )