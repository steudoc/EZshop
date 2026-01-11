from typing import List, Optional
from app.repositories.order_repository import OrderRepository
from app.models.DTO.order_dto import OrderDTO
from app.services.mapper_service import orderdao_to_dto
from app.models.errors.bad_request import BadRequestError
from app.models.order_status import OrderStatus


class OrderController:
    def __init__(self):
        self.repo = OrderRepository()

    async def _create_order(self, order_dto: OrderDTO) -> OrderDTO: 
        """Creates a new order for a given product"""
        if (
            (order_dto.quantity<=0) or
            (order_dto.price_per_unit<=0)
            # or (order_dto.id is not None and order_dto.id<=0)
        ): 
            raise BadRequestError('Incorrect parameters')
        
        order_dto.id = None
        created = await self.repo.create_order(order_dto.id, order_dto.product_barcode, order_dto.quantity, order_dto.price_per_unit, order_dto.status, order_dto.issue_date)
        return orderdao_to_dto(created)

    async def list_orders(self) -> List[OrderDTO]:
        """Returns all orders in the system"""
        daos = await self.repo.list_orders()
        return [orderdao_to_dto(dao) for dao in daos]
    
    async def create_issued_order(self, order_dto: OrderDTO) -> OrderDTO: 
        """Creates a new order that still needs to be paid"""
        order_dto.status = OrderStatus.ISSUED
        return await self._create_order(order_dto)

    async def create_paid_order(self, order_dto: OrderDTO) -> OrderDTO: 
        """Creates a new order and immediately pays for it"""      
        order_dto.status = OrderStatus.PAID
        return await self._create_order(order_dto)
        
    async def pay_order(self, order_id: int):
        """Pays an existing ISSUED order"""
        if order_id<=0:
            raise BadRequestError("Invalid order id")
        await self.repo.update_issued_order(order_id)
    
    async def complete_order(self, order_id: int):
        """Marks a PAID order as COMPLETED and updates product quantities"""
        if order_id<=0:
            raise BadRequestError("Invalid order id")
        await self.repo.update_paid_order(order_id)
