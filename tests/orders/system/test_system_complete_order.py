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
async def test_complete_order_system_workflow():
    """System test: Transition PAID order to COMPLETED and verify inventory restocking"""
    await reset_db()
    await init_db()
    
    # Setup: Create product with quantity 100 and system balance
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
    
    # Execute: Pay order
    await controller.pay_order(created_order.id)
    
    # Verify: Order is PAID, inventory unchanged
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.PAID
        
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.quantity == 100
    
    # Execute: Complete order
    await controller.complete_order(created_order.id)
    
    # Verify: Order is COMPLETED, inventory increased
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.COMPLETED
        
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.quantity == 105  # 100 + 5


@pytest.mark.asyncio
async def test_complete_order_restocks_correct_quantity():
    """System test: complete_order restocks exact quantity from order"""
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
            quantity=50,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute: Create, pay, and complete order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=12,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_issued_order(order_dto)
    await controller.pay_order(created_order.id)
    await controller.complete_order(created_order.id)
    
    # Verify: Exact quantity restocked
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.quantity == 62  # 50 + 12


@pytest.mark.asyncio
async def test_complete_order_preserves_balance():
    """System test: Completing order doesn't change system balance"""
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
    
    # Execute: Create, pay, and complete order
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
    await controller.pay_order(created_order.id)  # Balance becomes 950
    await controller.complete_order(created_order.id)
    
    # Verify: Balance unchanged by completion
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 950.0  # Still 950, not affected by complete


@pytest.mark.asyncio
async def test_complete_order_full_lifecycle():
    """System test: Complete order lifecycle from ISSUED to COMPLETED"""
    await reset_db()
    await init_db()
    
    # Setup
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=15.0,
            quantity=75,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(500.0)
        await session.commit()
    
    # Execute: Create order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=8,
        price_per_unit=15.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_issued_order(order_dto)
    
    # Verify: ISSUED state
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.ISSUED
        
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.quantity == 75
        
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 500.0
    
    # Execute: Pay order
    await controller.pay_order(created_order.id)
    
    # Verify: PAID state
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.PAID
        
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.quantity == 75  # Unchanged
        
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 380.0  # 500 - (8 * 15)
    
    # Execute: Complete order
    await controller.complete_order(created_order.id)
    
    # Verify: COMPLETED state with restocking
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        order = await order_repo.get_order(created_order.id)
        assert order.status == OrderStatus.COMPLETED
        
        product = await product_repo.get_product_by_barcode("4006381333931")
        assert product.quantity == 83  # 75 + 8
        
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 380.0  # Unchanged by completion


@pytest.mark.asyncio
async def test_complete_order_appears_in_list():
    """System test: Completed orders appear correctly in order list"""
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
    
    # Execute: Create, pay, and complete order
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
    await controller.complete_order(created_order.id)
    
    # Execute: List orders
    all_orders = await controller.list_orders()
    
    # Verify: Completed order in list with correct status
    assert len(all_orders) == 1
    assert all_orders[0].id == created_order.id
    assert all_orders[0].status == OrderStatus.COMPLETED
