from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.DAO.system_dao import SystemInfoDAO 
from app.database.database import AsyncSessionLocal
from app.utils import find_or_throw_not_found

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

    async def get_system_info(self, system_info_id: int) -> SystemInfoDAO:
        # TODO: aggiungere descrizione
        async with await self._get_session() as session:
            if system_info_id <= -1:
                result = await session.execute(
                    select(SystemInfoDAO).order_by(desc(SystemInfoDAO.id))
                )
            else:
                result = await session.execute(
                    select(SystemInfoDAO).where(SystemInfoDAO.id == system_info_id)
                )

            system_info = result.scalars().first()

            return find_or_throw_not_found(
                [system_info] if system_info else [],
                lambda _: True,
                f"System info with id '{system_info_id}' not found"
            )
        
    async def create_system_info(self, balance: float) -> SystemInfoDAO:
        # TODO: aggiungere descrizione
        async with await self._get_session() as session:
            system_info = SystemInfoDAO(balance=balance)
            session.add(system_info)
            await session.commit()
            await session.refresh(system_info)
            return system_info
        


    