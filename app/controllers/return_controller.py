""" Return Controller Module.
This module contains the ReturnController class which handles the business logic"""

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
from typing import List, Optional
from app.services.mapper_service import returndao_to_responsedto

class ReturnController:
    def __init__(self):
        self.repo = ReturnRepository()

    async def start_return(self, sale_id: int) -> ReturnDTO: 
        """Create return transaction - throws BadRequestError if sale invalid or not closed/paid"""
        created = await self.repo.start_return(sale_id)
        return returndao_to_responsedto(created)
    
    @staticmethod
    async def get_all_returns():
        return await ReturnRepository.get_all_returns()

    @staticmethod
    async def get_return_by_id(return_id: int):
        return_tx = await ReturnRepository.get_return_by_id(return_id)
        if not return_tx:
            raise NotFoundError("Return not found")
        return return_tx

    @staticmethod
    async def delete_return(return_id: int):
        deleted = await ReturnRepository.delete_return(return_id)
        if not deleted:
            raise NotFoundError("Return not found")

    @staticmethod
    async def get_returns_by_sale(sale_id: int):
        return await ReturnRepository.get_returns_by_sale(sale_id)

    @staticmethod
    async def add_item_to_return(return_id: int, item: ReturnItemDTO):
        return await ReturnRepository.add_item(return_id, item)

    @staticmethod
    async def remove_item_from_return(return_id: int, item: ReturnItemDTO):
        return await ReturnRepository.remove_item(return_id, item)

    @staticmethod
    async def close_return(return_id: int, data: ReturnCloseDTO):
        return await ReturnRepository.close_return(return_id, data)

    @staticmethod
    async def reimburse_return(return_id: int, data: ReturnReimburseDTO):
        # Find return transaction
        return_tx = await ReturnRepository.get_return_by_id(return_id)
        if not return_tx:
            raise NotFoundError("Return not found")

        # Compute refund amount
        amount = ReturnService.calculate_refund(return_tx)

        # Manage payment
        if data.payment_type == "cash":
            ReturnService.process_cash_refund(amount)
        elif data.payment_type == "credit_card":
            if not ReturnService.validate_credit_card(data.credit_card_number):
                raise PaymentFailedError("Invalid credit card")
            ReturnService.process_card_refund(amount, data.credit_card_number)
        else:
            raise BadRequestError("Invalid payment type")

        # Update return transaction status
        return await ReturnRepository.reimburse_return(return_id, amount)

