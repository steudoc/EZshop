from typing import List, Optional
from app.repositories.user_repository import UserRepository
from app.models.DTO.user_dto import UserDTO
from app.services.mapper_service import userdao_to_responsedto

class UserController:
    def __init__(self):
        self.repo = UserRepository()

    async def create_user(self, user_dto: UserDTO) -> UserDTO: 
        """Create user - throws ConflictError if username exists"""
        created = await self.repo.create_user(user_dto.username, user_dto.password, user_dto.type)
        return userdao_to_responsedto(created)

    async def get_user(self, user_id: int) -> Optional[UserDTO]:
        """Get user by username - throws NotFoundError if not found"""
        dao = await self.repo.get_user(user_id)
        return userdao_to_responsedto(dao) if dao else None

    async def list_users(self) -> List[UserDTO]:
        """Get all users"""
        daos = await self.repo.list_users()
        return [userdao_to_responsedto(dao) for dao in daos]

    async def update_user(self, user_id: int, user_dto: UserDTO) -> Optional[UserDTO]:
        """Update user - throws NotFoundError if user doesn't exist, ConflictError if new username exists"""
        updated = await self.repo.update_user(user_id, user_dto.username, user_dto.password, user_dto.type)
        return userdao_to_responsedto(updated) if updated else None

    async def delete_user(self, user_id: int) -> bool:
        """Delete user - throws NotFoundError if not found"""
        return await self.repo.delete_user(user_id)
