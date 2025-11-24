from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_type import UserType
from app.models.DAO.user_dao import UserDAO
from app.utils import throw_conflict_if_found, find_or_throw_not_found
from app.database.database import AsyncSessionLocal
from typing import Optional


class UserRepository:

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        return self._session or AsyncSessionLocal()

    async def create_user(self, username: str, password: str, user_type: UserType) -> UserDAO:
        """
        Create user or throw ConflictError if username exists
        """
        async with await self._get_session() as session:
            result = await session.execute(select(UserDAO).filter(UserDAO.username == username))
            existing_users = result.scalars().all()

            throw_conflict_if_found(
                existing_users,
                lambda _: True,
                f"User with username '{username}' already exists"
            )

            user = UserDAO(username=username, password=password, type=user_type)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_user(self, user_id: int) -> UserDAO | None:
        """
        Get user by id or throw NotFoundError if not found
        """
        async with await self._get_session() as session:
            user = await session.get(UserDAO, user_id)
            return find_or_throw_not_found(
                [user] if user else [],
                lambda _: True,
                f"User with id '{user_id}' not found"
            )

    async def get_user_by_username(self, username: str) -> UserDAO | None:
        """
        Get user by username or throw NotFoundError if not found
        """
        async with await self._get_session() as session:
            result = await session.execute(select(UserDAO).filter(UserDAO.username == username))
            users = result.scalars().all()
            return find_or_throw_not_found(
                users,
                lambda _: True,
                f"User with username '{username}' not found"
            )

    async def list_users(self) -> list[UserDAO]:
        """Get all users"""
        async with await self._get_session() as session:
            result = await session.execute(select(UserDAO))
            return result.scalars().all()

    async def update_user(self, user_id: int, updated_username: str, password: str, type: UserType) -> UserDAO | None:
        """
        Update user information. Throw NotFoundError if not found or ConflictError if the new username exists
        """
        async with await self._get_session() as session:
            db_user = await session.get(UserDAO, user_id)
            if not db_user:
                return None

            result_conflict = await session.execute(select(UserDAO).filter(UserDAO.username == updated_username))
            conflicting_username = result_conflict.scalars().all()
            throw_conflict_if_found(
                conflicting_username,
                lambda _: True,
                f"User with username '{updated_username}' already exists"
            )

            db_user.username = updated_username
            db_user.password = password
            db_user.type = type

            await session.commit()
            await session.refresh(db_user)
            return db_user

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete user by id. Will throw NotFoundError if user doesn't exist
        """
        async with await self._get_session() as session:
            user = await session.get(UserDAO, user_id)

            find_or_throw_not_found(
                [user] if user else [],
                lambda _: True,
                f"User with id '{user_id}' not found"
            )

            await session.delete(user)
            await session.commit()
            return True