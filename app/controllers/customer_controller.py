from typing import List, Optional
from app.repositories.customer_repository import CustomerRepository
from app.models.DTO.customer_dto import CustomerDTO, CardDTO, UpdateCustomerDTO
from app.services.mapper_service import customerdao_to_responsedto

class CustomerController:
    def __init__(self):
        self.repo = CustomerRepository()

    async def create_customer(self, customer_dto: CustomerDTO) -> CustomerDTO: 
        """Create customer"""


        customer, card = await self.repo.create_customer(customer_dto.name,  customer_dto.card)

        if card is not None:
            return CustomerDTO(
            id=customer.id,
            name=customer.name,
            card=CardDTO(
                card_id=card.cardId,
                points=card.points
                )
            )
        else:
            return CustomerDTO(
                id=customer.id,
                name=customer.name
            )
    
    async def attach_card_to_customer(self, customer_id=int, card_id=int) -> CustomerDTO: 
        """Attach a card with card_id to a customer with customer_id"""
        customer, card  = await self.repo.attach_card_to_customer(customer_id, card_id)

        return CustomerDTO(
            id=customer.id,
            name=customer.name,
            card=CardDTO(
                card_id=card.cardId,
                points=card.points
            )
        )
    

    async def delete_user(self, customer_id: int) -> bool: 
        """Delete a customer by customer_id, if a card is attached, the card will deleted as well"""
        return await self.repo.delete_user(customer_id)

    async def get_customer(self, customer_id: int) -> Optional[CustomerDTO]:
        """Get customer by id - throws NotFoundError if not found"""
        dao = await self.repo.get_customer(customer_id)
        return await customerdao_to_responsedto(dao) if dao else None
    

    async def list_customers(self) -> List[CustomerDTO]:
        """Get all customers"""
        daos = await self.repo.list_customers()
        return [await customerdao_to_responsedto(dao) for dao in daos]
    

    async def update_customer(self, customer_id: int, customer_dto: UpdateCustomerDTO) -> Optional[CustomerDTO]:
        """Update customer"""
        updated = await self.repo.update_customer(customer_id, customer_dto.name, customer_dto.card)
        return await customerdao_to_responsedto(updated) if updated else None