from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import AsyncSessionLocal

class BaseRepository:
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager that manages the session lifecycle.
        - If the session is external (passed in the constructor): It only performs FLUSH.
        - If the session is new (local): It performs COMMIT and CLOSE.
        - Automatically handles ROLLBACK in case of error.
        """
        is_local = False
        if self._session:
            session = self._session
        else:
            session = AsyncSessionLocal()
            is_local = True

        try:
            yield session
            
            # --- SUCCESS PHASE ---
            if is_local:
                await session.commit()
            else:
                # If it is external, we flush to ensure the data is visible 
                # (e.g. to generate IDs) but we do NOT close the transaction.
                await session.flush()
                
        except Exception:
            # --- ERROR PHASE ---
            if is_local:
                await session.rollback()
            raise  # Rethrow the error to be handled by the caller (e.g. controller)
            
        finally:
            # --- CLEANING PHASE ---
            if is_local:
                await session.close()