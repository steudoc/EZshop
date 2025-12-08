from sqlalchemy.ext.asyncio import AsyncSession
from app.models.DAO.card_dao import CardDAO
from app.database.database import AsyncSessionLocal
from app.utils import find_or_throw_not_found
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
    
    #TODO
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
