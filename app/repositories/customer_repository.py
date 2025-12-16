from sqlalchemy.ext.asyncio import AsyncSession
from app.models.DAO.customer_dao import CustomerDAO
from app.models.DAO.card_dao import CardDAO
from app.models.DTO.customer_dto import CardDTO
from app.database.database import AsyncSessionLocal
from typing import Optional
from app.utils import find_or_throw_not_found, throw_conflict
from app.repositories.card_repository import CardRepository

class CustomerRepository:

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()

    async def create_customer(
            self,
            name: str,
            card: CardDTO | None
    ) -> tuple[CustomerDAO, CardDAO]:
        """
        Create card
        """
        async with await self._get_session() as session:

            if card is not None:
                
                if await session.get(CardDAO, card.cardId) is not None:
                    throw_conflict("Card with id {card.cardId} is already attached to a customer")

                customer = CustomerDAO(name=name)
                card_dao = CardDAO(cardId=card.cardId, points=card.points, customer_id = customer.id)
                session.add(card_dao)
            else:
                customer = CustomerDAO(name=name)
            
            session.add(customer)
            await session.commit()
            await session.refresh(customer)

            if card is not None:
                await session.refresh(customer)

            return customer, card
        

    async def attach_card_to_customer(
        self,
        customer_id: int,
        card_id: int
    ) -> tuple[CustomerDAO, CardDAO]:

        async with await self._get_session() as session:

            customer = await session.get(CustomerDAO, customer_id)
            find_or_throw_not_found(
                [customer] if customer else [],
                lambda _: True,
                f"Customer with id '{customer_id}' not found"
            )

            card = await session.get(CardDAO, card_id)
            find_or_throw_not_found(
                [card] if card else [],
                lambda _: True,
                f"Card with id '{card_id}' not found"
            )

            if card.cardId is not None:
                throw_conflict("Card with id {card_id} is already attached to a customer")

            card.customer_id = customer_id
            await session.commit()
            await session.refresh(card)

            return customer, card
        
    async def delete_user(self, customer_id: int) -> CustomerDAO: 
        """Delete a customer by customer_id, if a card is attached, the card will deleted as well"""
        async with await self._get_session() as session:

            customer = await session.get(CustomerDAO, customer_id)
            find_or_throw_not_found(
                [customer] if customer else [],
                lambda _: True,
                f"Customer with id '{customer_id}' not found"
            )
            card = await CardRepository.get_card_by_customer(session, customer_id)
            if card is not None:
                await session.delete(card)

            await session.delete(customer)
            await session.commit()

            return customer
    

    async def get_customer(self, customer_id: int) -> CustomerDAO | None:
        """
        Get customer by id or throw NotFoundError if not found
        """
        async with await self._get_session() as session:
            user = await session.get(CustomerDAO, customer_id)
            return find_or_throw_not_found(
                [user] if user else [],
                lambda _: True,
                f"Customer with id '{customer_id}' not found"
            )