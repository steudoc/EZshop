from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.DAO.system_dao import SystemInfoDAO 
from app.database.database import AsyncSessionLocal

class SystemRepository:
    _instance: Optional["SystemRepository"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SystemRepository, cls).__new__(cls)
        return cls._instance

    def __init__(self, session: Optional[AsyncSession] = None):
        if not hasattr(self, "_initialized"):
            self._session = session
            self._initialized = True

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()

    async def get_last_system_info(self) -> SystemInfoDAO:
        """
        Retrieve the most recent system information entry.

        - Returns: the latest SystemInfoDAO entry ordered by ID descending
        """
        async with await self._get_session() as session:
            result = await session.execute(
                select(SystemInfoDAO).order_by(desc(SystemInfoDAO.id))
            )
            return result.scalars().first()
        
    async def create_system_info(self, balance: float) -> SystemInfoDAO:
        """
        Create a new system information entry.

        - Parameter: balance (float) - the balance value to store
        - Returns: the newly created SystemInfoDAO entry
        """
        async with await self._get_session() as session:
            system_info = SystemInfoDAO(balance=balance)
            session.add(system_info)
            await session.commit()
            await session.refresh(system_info)
            return system_info
        


    