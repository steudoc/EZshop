import pytest
from datetime import datetime
from app.controllers.order_controller import OrderController
from app.models.DTO.order_dto import OrderDTO
from app.models.order_status import OrderStatus
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository
from app.repositories.order_repository import OrderRepository


@pytest.mark.asyncio
async def test_list_orders_empty_system():
    """System test: list_orders returns empty list when no orders exist"""
    await reset_db()
    await init_db()
    
    # Execute: List orders from empty system
    controller = OrderController()
    orders = await controller.list_orders()
    
    # Verify: Empty list returned
    assert orders is not None
    assert len(orders) == 0


@pytest.mark.asyncio
async def test_list_orders_single_issued():
    """System test: list_orders returns single ISSUED order"""
    await reset_db()
    await init_db()
    
    # Setup: Create product and system balance
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute: Create one ISSUED order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_issued_order(order_dto)
    
    # Execute: List orders
    orders = await controller.list_orders()
    
    # Verify: Single order returned with correct details
    assert len(orders) == 1
    assert orders[0].id == created_order.id
    assert orders[0].status == OrderStatus.ISSUED
    assert orders[0].quantity == 5
    assert orders[0].price_per_unit == 10.0


@pytest.mark.asyncio
async def test_list_orders_multiple_mixed_status():
    """System test: list_orders returns multiple orders with different statuses"""
    await reset_db()
    await init_db()
    
    # Setup
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute: Create 3 orders with different statuses
    controller = OrderController()
    
    # ISSUED order
    issued_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    issued_order = await controller.create_issued_order(issued_dto)
    
    # PAID order
    paid_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=3,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    paid_order = await controller.create_paid_order(paid_dto)
    
    # COMPLETED order (first create ISSUED, then PAY, then COMPLETE)
    completed_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=2,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    completed_order = await controller.create_issued_order(completed_dto)
    await controller.pay_order(completed_order.id)
    await controller.complete_order(completed_order.id)
    
    # Execute: List all orders
    orders = await controller.list_orders()
    
    # Verify: All 3 orders returned with correct statuses
    assert len(orders) == 3
    
    # Check each order is present
    order_statuses = {order.id: order.status for order in orders}
    assert order_statuses[issued_order.id] == OrderStatus.ISSUED
    assert order_statuses[paid_order.id] == OrderStatus.PAID
    assert order_statuses[completed_order.id] == OrderStatus.COMPLETED


@pytest.mark.asyncio
async def test_list_orders_maintains_order_details():
    """System test: list_orders preserves all order details accurately"""
    await reset_db()
    await init_db()
    
    # Setup
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        await product_repo.create_product(
            barcode="4006381333931",
            description="Premium Product",
            price_per_unit=25.5,
            quantity=100,
            note="Test product",
            position="2-B-3"
        )
        
        await system_repo.create_system_info(5000.0)
        await session.commit()
    
    # Execute: Create order with specific details
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=12,
        price_per_unit=25.5,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_issued_order(order_dto)
    
    # Execute: List and verify details
    orders = await controller.list_orders()
    
    # Verify: All details preserved
    assert len(orders) == 1
    order = orders[0]
    assert order.id == created_order.id
    assert order.product_barcode == "4006381333931"
    assert order.quantity == 12
    assert order.price_per_unit == 25.5
    assert order.status == OrderStatus.ISSUED
    assert order.issue_date is not None


@pytest.mark.asyncio
async def test_list_orders_reflects_latest_state():
    """System test: list_orders reflects current state after order transitions"""
    await reset_db()
    await init_db()
    
    # Setup
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute: Create order and transition states
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_issued_order(order_dto)
    
    # List orders in ISSUED state
    orders = await controller.list_orders()
    assert orders[0].status == OrderStatus.ISSUED
    
    # Transition to PAID
    await controller.pay_order(created_order.id)
    orders = await controller.list_orders()
    assert orders[0].status == OrderStatus.PAID
    
    # Transition to COMPLETED
    await controller.complete_order(created_order.id)
    orders = await controller.list_orders()
    assert orders[0].status == OrderStatus.COMPLETED
