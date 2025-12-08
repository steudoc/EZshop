from typing import Optional
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
    

    async def modify_points_card(self, card_id, points) -> CardResponseDTO: 
        """Modify card points"""
        modified = await self.repo.update_card(card_id, points)
        return carddao_to_response_dto(modified)
    
    async def get_card(self, card_id) -> Optional[CardResponseDTO]:
        "Return a card given a card_id"
        card = await self.repo.get_card(card_id)
        return carddao_to_response_dto(card) if card else None
