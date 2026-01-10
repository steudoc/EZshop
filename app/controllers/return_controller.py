from app.repositories.return_repository import ReturnRepository
from app.models.DTO.return_dto import (
    ReturnDTO,
    ReturnCreateDTO,
    ReturnResponseDTO,
    ReturnItemDTO,
    ReturnCloseDTO,
    ReturnReimburseDTO
)
from app.models.errors.return_errors import (
    BadRequestError,
    NotFoundError,
    InvalidStateError,
    PaymentFailedError
)
from app.services.return_service import ReturnService
from app.controllers.system_controller import SystemController
from typing import List, Optional
from app.services.mapper_service import returndao_to_responsedto

class ReturnController:
    def __init__(self):
        self.repo = ReturnRepository()
        self.system_controller = SystemController()

    async def start_return(self, sale_id: int) -> ReturnDTO: 
        """Create return transaction - throws BadRequestError if sale invalid or not closed/paid"""
        created = await self.repo.start_return(sale_id)
        return returndao_to_responsedto(created)
    
    async def get_all_returns(self) -> List[ReturnDTO]:
        """Get all return transactions"""
        daos = await self.repo.get_all_returns()
        return [returndao_to_responsedto(dao) for dao in daos]
    
    async def get_return_by_id(self, return_id: int) -> Optional[ReturnDTO]:
        """Get return by return id - throws NotFoundError if not found"""
        dao = await self.repo.get_return_by_id(return_id)
        return returndao_to_responsedto(dao) if dao else None
        
    async def delete_return(self, return_id: int) -> bool:
        """Delete return - throws NotFoundError if not found"""
        return await self.repo.delete_return(return_id)

    async def get_returns_by_sale(self, sale_id: int) -> List[ReturnDTO]:
        """Get all returns by sale id"""
        daos = await self.repo.get_returns_by_sale(sale_id)
        return [returndao_to_responsedto(dao) for dao in daos]

    async def add_item(self, return_id: int, item: ReturnItemDTO) -> ReturnDTO:
        """Add item to return - throws NotFoundError if return or product not found, InvalidStateError if return not open"""
        updated = await self.repo.add_item(return_id, item)
        return returndao_to_responsedto(updated)

    async def remove_item(self, return_id: int, product_barcode: str, quantity: int) -> ReturnDTO:
        """Remove item from return - throws NotFoundError if return or product not found, InvalidStateError if return not open"""
        updated = await self.repo.remove_item(return_id, product_barcode, quantity)
        return returndao_to_responsedto(updated)

    async def close_return(self, return_id: int) -> Optional[ReturnDTO]:
        """Close return - throws NotFoundError if return not found, InvalidStateError if return not open
        If return is empty (has no items), it will be deleted instead of closed"""
        return_tx = await self.repo.get_return_by_id(return_id)
        if not return_tx:
            raise NotFoundError("Return not found")
        
        # If return is empty (no items), delete it instead of closing
        if not return_tx.lines or len(return_tx.lines) == 0:
            await self.repo.delete_return(return_id)
            return None
        
        # Otherwise, close the return normally
        closed_return = await self.repo.close_return(return_id)
        return returndao_to_responsedto(closed_return) if closed_return else None

    async def reimburse_return(self, return_id: int) -> ReturnReimburseDTO:
        # Find return transaction
        return_tx = await self.repo.get_return_by_id(return_id)
        if not return_tx:
            raise NotFoundError("Return not found")

        # Compute refund amount
        amount = ReturnService.calculate_refund(return_tx)

        # Update return transaction status (this will validate the status and throw if needed)
        await self.repo.reimburse_return(return_id)

        # Update system balance by deducting the refund amount
        current_balance = await self.system_controller.get_balance()
        new_balance = current_balance.balance - amount
        await self.system_controller.set_balance(new_balance)

        reimburse_dto = ReturnReimburseDTO(
            refund_amount=amount 
        )
        return reimburse_dto

