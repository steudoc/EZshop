import pytest
from datetime import datetime
from app.controllers.order_controller import OrderController
from app.models.DTO.order_dto import OrderDTO
from app.models.order_status import OrderStatus
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository


@pytest.mark.asyncio
async def test_list_orders_empty():
    """Test listing orders when database is empty"""
    await reset_db()
    await init_db()
    
    # Execute
    controller = OrderController()
    orders = await controller.list_orders()
    
    # Verify
    assert orders == []
    assert len(orders) == 0


@pytest.mark.asyncio
async def test_list_orders_single_issued():
    """Test listing orders with a single ISSUED order"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        
        # Setup: Create a product
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        await session.commit()
    
    # Create an order
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
    
    # Execute
    orders = await controller.list_orders()
    
    # Verify
    assert len(orders) == 1
    assert orders[0].id == created_order.id
    assert orders[0].product_barcode == "4006381333931"
    assert orders[0].quantity == 5
    assert orders[0].status == OrderStatus.ISSUED


@pytest.mark.asyncio
async def test_list_orders_multiple_same_product():
    """Test listing multiple orders for the same product"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product and system balance
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(2000.0)
        await session.commit()
    
    # Create multiple orders for the same product
    controller = OrderController()
    
    order_dtos = [
        OrderDTO(
            id=None,
            product_barcode="4006381333931",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        ),
        OrderDTO(
            id=None,
            product_barcode="4006381333931",
            quantity=10,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        ),
        OrderDTO(
            id=None,
            product_barcode="4006381333931",
            quantity=7,
            price_per_unit=10.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        ),
    ]
    
    created_orders = []
    for order_dto in order_dtos:
        if order_dto.status == OrderStatus.ISSUED:
            created_orders.append(await controller.create_issued_order(order_dto))
        else:
            created_orders.append(await controller.create_paid_order(order_dto))
    
    # Execute
    orders = await controller.list_orders()
    
    # Verify
    assert len(orders) == 3
    
    all_same_barcode = all(o.product_barcode == "4006381333931" for o in orders)
    assert all_same_barcode
    
    total_quantity = sum(o.quantity for o in orders)
    assert total_quantity == 22  # 5 + 10 + 7
