from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.DAO.card_dao import CardDAO
from app.database.database import AsyncSessionLocal
from app.models.errors.notfound_error import NotFoundError
from app.utils import find_or_throw_not_found, throw_not_found
from typing import Optional


class CardRepository:

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()

    async def create_card(self) -> CardDAO:
        """
        Create and store a customer card on the database.

        Returns:
            CardDAO: Instance of the newly created and saved card.
        """
        async with await self._get_session() as session:
            card = CardDAO(points=0)
            session.add(card)
            await session.commit()
            await session.refresh(card)
            return card
    
    async def get_card(self, card_id : int) -> CardDAO:
        """
        Retrieve a card by the given card_id.

        Args:
            card_id(int): Unique identifier of the card to retrieve.

        Returns:
            CardDAO: The requested card if found.

        Raises:
            NotFoundError: If no card with the given 'card_id' exists.
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, card_id)
            return find_or_throw_not_found(
                [card] if card else [],
                lambda _: True,
                f"Card with id '{card_id}' not found"
            )
        
    async def update_card(self, card_id: int, points: int) -> CardDAO:
        """
        Update card points of the card with id=card_id
        In this method we assume that |points| <= db_card.points

        Args:
            card_id(int): Unique identifier of the card to retrieve.
            points(int): Points to be added or decreased.

        Returns:
            CardDAO: The requested card if found.

        Raises:
            NotFoundError: If no card with the given 'card_id' exists.
        """
        async with await self._get_session() as session:
            db_card = await session.get(CardDAO, card_id)
            if not db_card:
                raise NotFoundError(f"Card with id '{card_id}' not found")
            
            db_card.cardId = card_id
            db_card.points = db_card.points+points

            await session.commit()
            await session.refresh(db_card)
            return db_card

    async def get_card_by_customer(self, customer_id: int) -> CardDAO:
        """
        Retrieve a card associated at the given customer with customer_id.

        Args:
            customer_id(int): Unique identifier of the customer.

        Returns:
            CardDAO: The requested card, associated at the given customer, if found.

        Raises:
            NotFoundError: If no card associated at the given customer with customer_id exists.
        """
        async with await self._get_session() as session:
            stmt = select(CardDAO).filter_by(customer_id=customer_id)
            result = await session.execute(stmt)
            card = result.scalars().first()

            if not card:
                raise NotFoundError(f"Customer card not found: no card associated with customer {customer_id}")
            return card
    
    async def get_card_by_customer_without_raise_notfounderror(self, customer_id: int) -> Optional[CardDAO]:
        """
        Retrieve a card associated at the given customer with customer_id.

        Args:
            customer_id(int): Unique identifier of the customer.

        Returns:
            Optional[CardDAO]: The requested card, associated at the given customer, if found.
        """
        async with await self._get_session() as session:
            stmt = select(CardDAO).filter_by(customer_id=customer_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    
    async def delete_card(self, card_id: int) -> bool:
        """
        Delete a card by the given card_id.

        Returns:
            True: if the card is deleted

        Raises:
            NotFoundError: If no card with the given 'card_id' exists.
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, card_id)
            if not card:
                raise NotFoundError(f"Card with id '{card_id}' not found")
            await session.delete(card)
            await session.commit()
            return True
        
    async def create_and_attach_new_card_to_customer(self, customer_id: int, cardId: int, points: int) -> CardDAO:
        """
        Create a new card and attach it to customer with customer_id.

        Returns:
            CardDAO: Instance of the newly created and saved card.
        """
        async with await self._get_session() as session:
            new_card = CardDAO(
                cardId=cardId,
                points=points,
                customer_id=customer_id
            )
            session.add(new_card)
            await session.commit()
            await session.refresh(new_card)
            return new_card
    
    async def update_and_attach_card_to_customer(self, customer_id: int, cardId: int, points: int) -> CardDAO:
        """
        Attach an already created card with (card_id ) to customer with customer_id.

        This method can update the points on the card.
        Returns:
            CardDAO: The requested card if found.
        Raises:
            NotFoundError: If no card with the given 'card_id' exists.
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, cardId)
            if not card:
                raise NotFoundError(f"Card with id '{cardId}' not found")
            
            card.cardId = cardId
            card.points = points
            card.customer_id = customer_id

            await session.commit()
            await session.refresh(card)
            return card
        
    async def is_attached(self, card_id: int) -> bool:
        """
        Check if a card is attached to a customer

        Returns:
            bool: if true, the card is attached to a customer

        Raises: 
            NotFoundError: If no card with the given 'card_id' exists.
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, card_id)
            if not card:
                raise NotFoundError(f"Card with id '{card_id}' not found")
            return card.customer_id is not None
        
    async def update_card_without_sum(self, card_id: int, points: int) -> CardDAO:
        """
        Update card points of the card with id=card_id.

        Args:
            card_id(int): Unique identifier of the card to retrieve.
            points(int): Points to be substitues.

        Returns:
            CardDAO: The requested card if found.

        Raises:
            NotFoundError: If no card with the given 'card_id' exists.
        """
        async with await self._get_session() as session:
            db_card = await session.get(CardDAO, card_id)
            if not db_card:
                raise NotFoundError(f"Card with id '{card_id}' not found")
            
            db_card.cardId = card_id
            db_card.points = points

            await session.commit()
            await session.refresh(db_card)
            return db_card