
from app.models.DTO.card_dto import CardResponseDTO
from app.repositories.card_repository import CardRepository
from app.services.mapper_service import carddao_to_response_dto

class CardController:
    def __init__(self):
        self.repo = CardRepository()

    async def create_card(self) -> CardResponseDTO: 
        """Create card"""
        created = await self.repo.create_card()
        return carddao_to_response_dto(created)