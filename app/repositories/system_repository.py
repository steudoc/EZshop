from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

    async def get_singleton(self) -> SystemInfoDAO:
        """Return the single SystemInfoDAO instance, create it if not existing."""
        async with await self._get_session() as session:
            result = await session.execute(select(SystemInfoDAO))
            system_info = result.scalars().first()

            if not system_info:
                system_info = SystemInfoDAO(balance=0.0)
                session.add(system_info)
                await session.commit()
                await session.refresh(system_info)

            return system_info