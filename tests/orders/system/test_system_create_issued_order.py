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
async def test_create_issued_order_system_workflow():
    """System test: Create ISSUED order and verify system state"""
    await reset_db()
    await init_db()
    
    # Setup: Create product
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        await session.commit()
    
    # Execute: Create ISSUED order
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
    
    # Verify: Order is created and persisted
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        retrieved_order = await order_repo.get_order(created_order.id)
        
        assert retrieved_order is not None
        assert retrieved_order.status == OrderStatus.ISSUED
        assert retrieved_order.product_barcode == "4006381333931"
        assert retrieved_order.quantity == 5
        assert retrieved_order.price_per_unit == 10.0


@pytest.mark.asyncio
async def test_create_issued_order_with_product_involvement():
    """System test: Create ISSUED order marks product as involved"""
    await reset_db()
    await init_db()
    
    # Setup
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        
        product = await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        assert product.involvedOperations == 0
        await session.commit()
    
    # Execute: Create ISSUED order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    await controller.create_issued_order(order_dto)
    
    # Verify: Product is marked as involved
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.involvedOperations > 0


@pytest.mark.asyncio
async def test_create_issued_order_does_not_affect_balance():
    """System test: Creating ISSUED order does not affect system balance"""
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
    
    # Get initial balance
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        initial_info = await system_repo.get_last_system_info()
        initial_balance = initial_info.balance
    
    # Execute: Create ISSUED order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    await controller.create_issued_order(order_dto)
    
    # Verify: Balance is unchanged
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        final_info = await system_repo.get_last_system_info()
        assert final_info.balance == initial_balance
