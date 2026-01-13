import math
from typing import Optional, List
from app.controllers.system_controller import SystemController
from app.models.DTO.boolean_dto import BooleanDTO
from app.models.sale_status import SaleStatus
from app.repositories.sale_repository import SaleRepository
from app.models.DTO.sale_dto import SaleChangeDTO, SaleDTO, SaleDiscountDTO, SaleLineDiscountDTO, SalePaymentDTO, SalePointsDTO, SaleLineDTO
from app.services.mapper_service import sale_dao_to_dto
from app.utils import throw_bad_request, throw_invalid_state, throw_not_found
from app.repositories.product_repository import ProductRepository

class SaleController:
    _instance: Optional["SaleController"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SaleController, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.sale_repo = SaleRepository()
        self.system_controller = SystemController()

    # ==============================================================================
    # PRIVATE HELPER METHODS
    # ==============================================================================

    async def _get_sale_or_throw(self, sale_id: int):
        """Helper to fetch sale or throw NotFoundError if missing"""
        sale_dao = await self.sale_repo.get_sale_by_id(sale_id)
        if not sale_dao:
            throw_not_found("Sale not found")
        return sale_dao

    def _validate_sale_status(self, sale_dao, expected_status: SaleStatus) -> None:
        """Helper to validate sale status - throws InvalidStateError if mismatch"""
        if sale_dao.status != expected_status:
            throw_invalid_state(f"Sale is not in {expected_status.name} state")

    # ==============================================================================
    # PUBLIC METHODS
    # ==============================================================================

    async def list_sales(self) -> list[SaleDTO]:
        """List all sales"""
        sales_daos = await self.sale_repo.list_sales()
        # Clean list comprehension with filter logic
        sales_dtos = [
            sale_dao_to_dto(sale_dao) 
            for sale_dao in sales_daos 
            if sale_dao is not None and sale_dao_to_dto(sale_dao) is not None
        ]
        return sales_dtos

    async def create_sale(self) -> SaleDTO:
        """Create a new sale"""
        sale_dao = await self.sale_repo.create_sale()
        return sale_dao_to_dto(sale_dao)

    async def get_sale(self, sale_id: int) -> SaleDTO:
        """Get a sale by ID - throws NotFoundError if not found"""
        sale_dao = await self._get_sale_or_throw(sale_id)
        return sale_dao_to_dto(sale_dao)

    async def delete_sale(self, sale_id: int) -> None:
        """Delete a sale by ID - throws NotFoundError if not found, BadRequestError if sale is PAID"""
        sale_dao = await self._get_sale_or_throw(sale_id)
        
        # Unique logic for delete: cannot be PAID (OPEN or PENDING is usually okay to delete)
        
        if sale_dao.status == SaleStatus.PAID:
            throw_invalid_state("Cannot delete this sale")
            
        await self.sale_repo.delete_sale(sale_id)

    async def add_item_to_sale(self, item_dto: SaleLineDTO) -> None:
        """Add a line to a sale - throws NotFoundError if sale missing, InvalidStateError if not OPEN"""
        sale_dao = await self._get_sale_or_throw(item_dto.sale_id)
        self._validate_sale_status(sale_dao, SaleStatus.OPEN)
        
        await self.sale_repo.add_item_to_sale(
            item_dto.sale_id, 
            item_dto.product_barcode, 
            item_dto.quantity
        )

    async def delete_item_from_sale(self, item_dto: SaleLineDTO) -> BooleanDTO:
        """Remove a line from a sale - throws NotFoundError if sale missing, InvalidStateError if not OPEN"""
        sale_dao = await self._get_sale_or_throw(item_dto.sale_id)
        self._validate_sale_status(sale_dao, SaleStatus.OPEN)

        
        sale_lines = next((l for l in sale_dao.lines if l.product_barcode == item_dto.product_barcode), None)

        if not sale_lines:
            throw_not_found("Product in sale line  not found")

        if not sale_lines or sale_lines.quantity < item_dto.quantity:
            throw_bad_request("Not enough quantity in sale line to remove")

        await self.sale_repo.remove_item_from_sale(
            item_dto.sale_id, 
            item_dto.product_barcode, 
            item_dto.quantity
        )
        return BooleanDTO(value=True)
    async def update_sale_discount(self, sale_discount_dto: SaleDiscountDTO) -> BooleanDTO:
        """Update sale discount - throws NotFoundError if sale missing, InvalidStateError if not OPEN"""
        sale_dao = await self._get_sale_or_throw(sale_discount_dto.id)
        self._validate_sale_status(sale_dao, SaleStatus.OPEN)
        
        result = await self.sale_repo.update_sale_discount(
            sale_discount_dto.id, 
            sale_discount_dto.discount_rate
        )
        
        if not result:
            throw_bad_request("Failed to update discount")
        return BooleanDTO(value=True)

    async def update_sale_line_discount(self, item_sale_dto: SaleLineDiscountDTO) -> BooleanDTO:
        """Update sale line discount - throws NotFoundError if sale missing, InvalidStateError if not OPEN"""
        sale_dao = await self._get_sale_or_throw(item_sale_dto.sale_id)
        self._validate_sale_status(sale_dao, SaleStatus.OPEN)
        
        result = await self.sale_repo.update_sale_line_discount(
            item_sale_dto.sale_id, 
            item_sale_dto.product_barcode, 
            item_sale_dto.discount_rate
        )
        
        if not result:
            throw_bad_request("Failed to update discount for sale line")
        return BooleanDTO(value=True)

    async def close_sale(self, sale_id: int) -> BooleanDTO:
        """Close a sale (set to PENDING) - throws NotFoundError if sale missing, InvalidStateError if not OPEN"""
        sale_dao = await self._get_sale_or_throw(sale_id)
        self._validate_sale_status(sale_dao, SaleStatus.OPEN)
        
        result = await self.sale_repo.update_sale_status_pending(sale_id)
        
        if not result:
            throw_bad_request("Failed to close sale")
        return BooleanDTO(value=True)

    async def process_payment(self, sale_payment_dto: SalePaymentDTO) -> SaleChangeDTO:
        """Process payment - throws NotFoundError if sale missing, InvalidStateError if not PENDING"""
        system_info = await self.system_controller.get_balance()
        sale_dao = await self._get_sale_or_throw(sale_payment_dto.sale_id)
        self._validate_sale_status(sale_dao, SaleStatus.PENDING)

        # Calculate Total
        total_price = 0.0
        for line in sale_dao.lines:
            partial_price = line.quantity * (line.price_per_unit - (line.price_per_unit * line.discount_rate))
            total_price += partial_price
            
        final_price = total_price - (total_price * sale_dao.discount_rate)

        
        if sale_payment_dto.amount_paid < final_price:
            throw_bad_request("Insufficient amount paid")


        change = sale_payment_dto.amount_paid - final_price

        await self.sale_repo.update_sale_status_paid(sale_payment_dto.sale_id)
        await self.system_controller.set_balance(system_info.balance + final_price)
        
        return SaleChangeDTO(change=change)

    async def get_sale_points(self, sale_id: int) -> SalePointsDTO:
        """Compute loyalty points - throws NotFoundError if sale missing, InvalidStateError if not PAID"""
        sale_dao = await self._get_sale_or_throw(sale_id)
        self._validate_sale_status(sale_dao, SaleStatus.PAID)
        
        points_base = 0
        for line in sale_dao.lines:
            points_base += line.quantity * line.price_per_unit 

        total_points = math.floor(points_base / 10)
        return SalePointsDTO(points=total_points)