from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.DAO.customer_dao import CustomerDAO
from app.models.DAO.card_dao import CardDAO
from app.models.DTO.customer_dto import CardDTO, UpdateCardDTO
from app.database.database import AsyncSessionLocal
from typing import Optional
from app.utils import find_or_throw_not_found, throw_conflict, throw_not_found
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
                
                if await session.get(CardDAO, card.card_id) is not None:
                    throw_conflict("Card with id {card.cardId} is already attached to a customer")

                customer = CustomerDAO(name=name)
                card_dao = CardDAO(cardId=card.card_id, points=card.points, customer_id = customer.id)
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

            if card.customer_id is not None:
                throw_conflict("Card with id {card_id} is already attached to a customer")

            card.customer_id = customer_id
            await session.commit()
            await session.refresh(card)

            return customer, card
        
    async def delete_user(self, customer_id: int) -> bool: 
        """Delete a customer by customer_id, if a card is attached, the card will deleted as well"""
        async with await self._get_session() as session:
            customer = await session.get(CustomerDAO, customer_id)
            find_or_throw_not_found(
                [customer] if customer else [],
                lambda _: True,
                f"Customer with id '{customer_id}' not found"
            )
            cardRepository_instance = CardRepository(session=session)
            card = await cardRepository_instance.get_card_by_customer(customer_id)
            if card is not None:
                await session.delete(card)

            await session.delete(customer)
            await session.commit()
            return True
    

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
        

    async def list_customers(self) -> list[CustomerDAO]:
        """Get all customers"""
        async with await self._get_session() as session:
            result = await session.execute(select(CustomerDAO))
            return result.scalars().all()
        
    async def update_customer(self, customer_id: int, updated_name: str, updated_card: UpdateCardDTO) -> CustomerDAO | None:
        """
        Update customer information.
        """
        async with await self._get_session() as session:
            db_customer = await session.get(CustomerDAO, customer_id)
            if not db_customer:
                return None

            cardRepository_instance = CardRepository(session=session)

            if updated_card is None:
                pass
            elif updated_card.cardId is None:
                # remove card if it exists
                card = await cardRepository_instance.get_card_by_customer(customer_id)
                if card is not None:
                    await session.delete(card)
            else:
                body_card_dao = await cardRepository_instance.get_card_by_id(updated_card.cardId)
                customer_card_dao = await cardRepository_instance.get_card_by_customer(customer_id)


                if body_card_dao is None:
                    # the updated card does not exist
                    if customer_card_dao is not None:
                        # the customer already had a card, remove it and attach the new one
                        await cardRepository_instance.delete_card(customer_card_dao.cardId)
                        await cardRepository_instance.create_and_attach_new_card_to_customer(customer_id, updated_card.cardId, updated_card.points) #TODO
                    else:
                        # the customer had not a card, attach the new one
                        await cardRepository_instance.create_and_attach_new_card_to_customer(customer_id, updated_card.cardId, updated_card.points)
                else:
                    # the updated card existed

                    if customer_id != body_card_dao.customer_id and await cardRepository_instance.is_attached(body_card_dao.cardId) is True:
                        throw_conflict(f"Card with id {updated_card.cardId} is already attached to another customer")
                    if customer_card_dao is not None:
                        # the customer already has a card
                        if body_card_dao.cardId != customer_card_dao.cardId:
                            # the card is different, remove the old one and attach the new one
                            await cardRepository_instance.delete_card(customer_card_dao.cardId)
                            await cardRepository_instance.update_and_attach_card_to_customer(customer_id, body_card_dao.cardId, updated_card.points)
                        else:
                            # the card is the same, just update the points
                            await cardRepository_instance.update_card_without_sum(body_card_dao.cardId, updated_card.points)
                    else:
                        # the customer had not a card, attach the existing one
                        await cardRepository_instance.update_and_attach_card_to_customer(customer_id, updated_card.cardId, updated_card.points)
                
            db_customer.name = updated_name
            await session.flush()
            await session.commit()

            return await self.get_customer(customer_id)