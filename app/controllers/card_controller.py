from typing import Optional
from app.models.DTO.customer_dto import CardDTO
from app.repositories.card_repository import CardRepository
from app.services.mapper_service import carddao_to_response_dto

class CardController:
    def __init__(self):
        self.repo = CardRepository()

    async def create_card(self) -> CardDTO: 
        """Create card"""
        created = await self.repo.create_card()
        return carddao_to_response_dto(created)
    

    async def modify_points_card(self, card_id, points) -> CardDTO: 
        """Modify card points"""
        modified = await self.repo.update_card(card_id, points)
        return carddao_to_response_dto(modified)
    
    async def get_card(self, card_id) -> Optional[CardDTO]:
        "Return a card given a card_id"
        card = await self.repo.get_card(card_id)
        return carddao_to_response_dto(card) if card else None
