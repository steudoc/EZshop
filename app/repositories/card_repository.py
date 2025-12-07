from sqlalchemy.ext.asyncio import AsyncSession
from app.models.DAO.card_dao import CardDAO
from app.database.database import AsyncSessionLocal
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
