from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.DAO.system_dao import SystemInfoDAO 
from app.database.database import AsyncSessionLocal
from app.repositories.base_repository import BaseRepository

class SystemRepository(BaseRepository):

    async def get_last_system_info(self) -> SystemInfoDAO | None:
        """
        Retrieve the most recent system information entry.

        - Returns: the latest SystemInfoDAO entry ordered by ID descending
        """
        async with self.get_session() as session:
            # get system info
            result = await session.execute(
                select(SystemInfoDAO).order_by(desc(SystemInfoDAO.id))
            )
            system_info = result.scalars().first()

            return system_info
        
    async def create_system_info(self, balance: float) -> SystemInfoDAO:
        """
        Create a new system information entry.

        - Parameter: balance (float) - the balance value to store
        - Returns: the newly created SystemInfoDAO entry
        """
        async with self.get_session() as session:

            system_info = SystemInfoDAO(balance=balance)
            session.add(system_info)

            await session.flush() # send insert to db
            await session.refresh(system_info)

            return system_info
        


    