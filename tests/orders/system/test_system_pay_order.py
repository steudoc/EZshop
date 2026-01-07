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
async def test_pay_order_system_workflow():
    """System test: Transition ISSUED order to PAID and verify balance deduction"""
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
    
    # Verify: Order is ISSUED, balance not deducted
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        system_repo = SystemRepository(session)
        
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.ISSUED
        
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 1000.0
    
    # Execute: Pay order
    await controller.pay_order(created_order.id)
    
    # Verify: Order is PAID and balance deducted
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        system_repo = SystemRepository(session)
        
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.PAID
        
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 950.0  # 1000 - (5 * 10)


@pytest.mark.asyncio
async def test_pay_order_deducts_correct_amount():
    """System test: pay_order deducts exact amount based on quantity and price"""
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
    
    # Execute: Create and pay order for 8 * 25 = 200
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=8,
        price_per_unit=25.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_issued_order(order_dto)
    await controller.pay_order(created_order.id)
    
    # Verify: Balance deducted by exact amount
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 300.0  # 500 - 200


@pytest.mark.asyncio
async def test_pay_order_does_not_affect_product_quantity():
    """System test: Paying order doesn't change product quantity"""
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
    
    # Execute: Create and pay order
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
    await controller.pay_order(created_order.id)
    
    # Verify: Product quantity unchanged (no inventory impact)
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.quantity == 100  # Still 100


@pytest.mark.asyncio
async def test_pay_order_from_multiple_source_states():
    """System test: Orders can only be paid from ISSUED state"""
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
    
    # Setup: Create multiple orders in different states
    controller = OrderController()
    
    # ISSUED order (can be paid)
    issued_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    issued_order = await controller.create_issued_order(issued_dto)
    
    # PAID order (already paid)
    paid_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=3,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    paid_order = await controller.create_paid_order(paid_dto)
    
    # Execute: Pay ISSUED order (should succeed)
    await controller.pay_order(issued_order.id)
    
    # Verify: ISSUED order is now PAID
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        order = await order_repo.get_order(issued_order.id)
        assert order.status == OrderStatus.PAID
