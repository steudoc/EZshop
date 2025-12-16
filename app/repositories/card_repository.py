from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.DAO.card_dao import CardDAO
from app.database.database import AsyncSessionLocal
from app.utils import find_or_throw_not_found, throw_not_found
from typing import Optional


class CardRepository:

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()

    async def create_card(self) -> CardDAO:
        """
        Create card
        """
        async with await self._get_session() as session:
            card = CardDAO(points=0)
            session.add(card)
            await session.commit()
            await session.refresh(card)
            return card
    
    async def get_card(self, card_id : int) -> CardDAO | None:
        """
        Get card given a card_id
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, card_id)
            return find_or_throw_not_found(
                [card] if card else [],
                lambda _: True,
                f"Customer Card not found"
            )
        
    async def update_card(self, card_id: int, points: int) -> CardDAO | None:
        """
        Update card information
        """
        async with await self._get_session() as session:
            db_card = await session.get(CardDAO, card_id)
            if not db_card:
                return None
            
            db_card.cardId = card_id
            db_card.points = db_card.points+points

            await session.commit()
            await session.refresh(db_card)
            return db_card

    async def get_card_by_customer(self, customer_id: int) -> Optional[CardDAO]:

        async with await self._get_session() as session:
            stmt = select(CardDAO).filter_by(customer_id=customer_id)
            result = await session.execute(stmt)
            return result.scalars().first()
        
    async def get_card_by_id(self, card_id: int) -> Optional[CardDAO]:

        async with await self._get_session() as session:
            stmt = select(CardDAO).filter_by(cardId=card_id)
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def delete_card(self, card_id: int) -> bool:
        """
        Delete card by card_id
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, card_id)
            if not card:
                return False
            await session.delete(card)
            await session.commit()
            return True
        
    async def create_and_attach_new_card_to_customer(self, customer_id: int, cardId: int, points: int) -> CardDAO:
        """
        Create a new card and attach it to customer
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
        Update and attach card to customer
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, cardId)
            if not card:
                throw_not_found(f"Card with id '{cardId}' not found")
            
            card.cardId = cardId
            card.points = points
            card.customer_id = customer_id

            await session.commit()
            await session.refresh(card)
            return card
        
    async def is_attached(self, card_id: int) -> bool:
        """
        Check if a card is attached to a customer
        """
        async with await self._get_session() as session:
            card = await session.get(CardDAO, card_id)
            if not card:
                throw_not_found(f"Card with id '{card_id}' not found")
            return card.customer_id is not None
        

    async def update_card_without_sum(self, card_id: int, points: int) -> CardDAO | None:
        """
        Update card information
        """
        async with await self._get_session() as session:
            db_card = await session.get(CardDAO, card_id)
            if not db_card:
                return None
            
            db_card.cardId = card_id
            db_card.points = points

            await session.commit()
            await session.refresh(db_card)
            return db_card