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
async def test_create_paid_order_system_workflow():
    """System test: Create PAID order and verify system state"""
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
    
    # Execute: Create PAID order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_paid_order(order_dto)
    
    # Verify: Order is created as PAID and balance is deducted
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        system_repo = SystemRepository(session)
        
        retrieved_order = await order_repo.get_order(created_order.id)
        assert retrieved_order is not None
        assert retrieved_order.status == OrderStatus.PAID
        
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 950.0  # 1000 - (5 * 10)


@pytest.mark.asyncio
async def test_create_paid_order_deducts_balance():
    """System test: Creating PAID order correctly deducts balance"""
    await reset_db()
    await init_db()
    
    # Setup
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=25.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(500.0)
        await session.commit()
    
    # Execute: Create PAID order for 8 units at 25 each = 200
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=8,
        price_per_unit=25.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    await controller.create_paid_order(order_dto)
    
    # Verify: Balance deducted correctly
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 300.0  # 500 - 200

@pytest.mark.asyncio
async def test_create_paid_order_marks_product_involved():
    """System test: Creating PAID order marks product as involved"""
    await reset_db()
    await init_db()
    
    # Setup
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        product = await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        assert product.involvedOperations == 0
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute: Create PAID order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    await controller.create_paid_order(order_dto)
    
    # Verify: Product is marked as involved
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.involvedOperations > 0


@pytest.mark.asyncio
async def test_create_paid_order_overrides_status():
    """System test: create_paid_order always sets status to PAID"""
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
    
    # Execute: Create order with ISSUED status, but use create_paid_order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,  # Try to set as ISSUED
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_paid_order(order_dto)
    
    # Verify: Order is PAID, not ISSUED
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_create_paid_order_appears_in_list():
    """System test: PAID orders appear in list_orders output"""
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
    
    # Execute: Create PAID order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_paid_order(order_dto)
    
    # Verify: Order appears in list
    all_orders = await controller.list_orders()
    
    assert len(all_orders) == 1
    assert all_orders[0].id == created_order.id
    assert all_orders[0].status == OrderStatus.PAID
