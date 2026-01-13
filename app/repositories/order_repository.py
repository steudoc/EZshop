from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order_status import OrderStatus
from app.models.DAO.order_dao import OrderDAO
from app.database.database import AsyncSessionLocal
from typing import Optional
from datetime import datetime
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.balance_error import BalanceError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.general_error import GeneralError
from app.models.errors.conflict_error import ConflictError
from app.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    """
    Repository for managing Order entities.
    Handles the lifecycle of orders including creation, listing, and state transitions
    (Issued -> Paid -> Completed), ensuring consistency with Product inventory and System balance.
    """

    async def _update_balance(self, system_repository: SystemRepository, amount: float):
        # check balance
        system_info = await system_repository.get_last_system_info()
        if system_info is None:
            raise NotFoundError("System info not found")
        # check balance value
        if system_info.balance < amount:
            raise BalanceError("Insufficient balance for the operation")
        # update balance
        await system_repository.create_system_info(system_info.balance-amount)

    async def create_order(self, id: int, product_barcode: str, quantity: int, price_per_unit: float, status: OrderStatus, issue_date: datetime) -> OrderDAO:
        """
        Creates a new order in the system.

        This operation is atomic and involves multiple checks:
        - Verifies if the product exists.
        - Updates the product involvement in operations.
        - If the status is PAID, it checks the system balance and deducts the total cost.

        Args:
            id (int): The unique identifier for the order.
            product_barcode (str): The barcode of the product to order.
            quantity (int): The number of units ordered.
            price_per_unit (float): The price per single unit.
            status (OrderStatus): The initial status of the order (ISSUED, PAID, etc.).
            issue_date (datetime): The date when the order was issued.

        Returns:
            OrderDAO: The newly created order object with updated database state.

        Raises:
            NotFoundError: If the product with the given barcode does not exist.
            BalanceError: If the status is PAID and the system balance is insufficient.
        """
        async with self.get_session() as session:

            product_repository = ProductRepository(session)

            # check order
            #if id is not None:
            #    order = await session.get(OrderDAO, id)
            #    if order is not None:
            #        raise ConflictError(f'An order with id={id} already exists')

            # check product
            product = await product_repository.get_product_by_barcode(product_barcode)
            if product is None:
                raise NotFoundError('Product not found')
            
            # update product
            await product_repository.include_product_in_op(product.id, True)

            if status == OrderStatus.PAID:
                system_repository = SystemRepository(session)
                await self._update_balance(system_repository, quantity*price_per_unit)

            order = OrderDAO(id=id, product_barcode=product_barcode, quantity=quantity, price_per_unit=price_per_unit, status=status, issue_date=issue_date)
            session.add(order)

            await session.flush()
            await session.refresh(order)
            return order
        
    async def list_orders(self) -> list[OrderDAO]:
        """
        Retrieves a list of all orders present in the database.

        Returns:
            list[OrderDAO]: A list of OrderDAO objects. Returns an empty list if no orders exist.
        """
        async with self.get_session() as session:
            result = await session.execute(select(OrderDAO))
            return result.scalars().all()

    async def get_order(self, order_id: int) -> OrderDAO | None:
        """
        Retrieves a specific order by its unique ID.

        Args:
            order_id (int): The unique identifier of the order.

        Returns:
            OrderDAO | None: The order object if found, otherwise None.
        """
        async with self.get_session() as session:
            order = await session.get(OrderDAO, order_id)
            return order

    async def update_issued_order(self, order_id: int) -> OrderDAO | None:
        """
        Transitions an order from ISSUED to PAID state.

        Performs the following actions atomically:
        - Verifies the order exists and is in ISSUED state.
        - Checks if the system balance covers the order cost.
        - Deducts the cost from the system balance.
        - Updates the order status to PAID.

        Args:
            order_id (int): The ID of the order to update.

        Returns:
            OrderDAO: The updated order object.

        Raises:
            NotFoundError: If the order does not exist.
            InvalidStateError: If the order is not in ISSUED state.
            BalanceError: If the system balance is insufficient to pay for the order.
        """
        async with self.get_session() as session:

            # check order
            order = await session.get(OrderDAO, order_id)
            if order is None:
                raise NotFoundError('Order not found')
            
            # check order status
            if order.status != OrderStatus.ISSUED:
                raise InvalidStateError('Order was not Issued')
            
            system_repository = SystemRepository(session)
            await self._update_balance(system_repository, order.quantity*order.price_per_unit)
            
            order.status = OrderStatus.PAID

            await session.flush()
            await session.refresh(order)
            return order

    async def update_paid_order(self, order_id: int) -> OrderDAO | None:
        """
        Transitions an order from PAID to COMPLETED state.

        Performs the following actions atomically:
        - Verifies the order exists and is in PAID state.
        - Verifies the associated product exists and has a valid position assigned.
        - Updates the order status to COMPLETED.
        - Restocks the product inventory (increments quantity).

        Args:
            order_id (int): The ID of the order to update.

        Returns:
            OrderDAO: The updated order object.

        Raises:
            NotFoundError: If the order or the associated product does not exist.
            InvalidStateError: If the order is not in PAID state.
            GeneralError: If the product does not have a valid position set (required for arrival).
        """
        async with self.get_session() as session:

            product_repository = ProductRepository(session)

            # check order
            order = await session.get(OrderDAO, order_id)
            if order is None:
                raise NotFoundError('Order not found')
            
            # check order status
            if order.status != OrderStatus.PAID:
                raise InvalidStateError('Order was not Issued')
            
            # check product
            product = await product_repository.get_product_by_barcode(order.product_barcode)
            if product is None:
                raise NotFoundError('Product not found')
            
            # check product position
            if not product_repository.is_position_valid(product.position, False):
                raise GeneralError("Position must be set for an order before its arrival")

            order.status = OrderStatus.COMPLETED
            product.quantity += order.quantity
            await product_repository.update_product(product)

            await session.flush()
            await session.refresh(order)
            return order