import pytest
from datetime import datetime
from app.controllers.order_controller import OrderController
from app.models.DTO.order_dto import OrderDTO
from app.models.order_status import OrderStatus
from app.models.errors.bad_request import BadRequestError
from app.models.errors.balance_error import BalanceError
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository


@pytest.mark.asyncio
async def test_create_paid_order_success():
    """Test successfully creating a PAID order"""
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
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute
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
    
    # Verify
    assert created_order.id is not None
    assert created_order.product_barcode == "4006381333931"
    assert created_order.quantity == 5
    assert created_order.price_per_unit == 10.0
    assert created_order.status == OrderStatus.PAID
    assert created_order.issue_date is not None
    
    # Verify balance was deducted
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 950.0  # 1000 - (5 * 10)


@pytest.mark.asyncio
async def test_create_paid_order_with_zero_quantity():
    """Test creating a PAID order with zero quantity raises BadRequestError"""
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
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=0,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.create_paid_order(order_dto)
    
    assert "Incorrect parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_paid_order_insufficient_balance():
    """Test creating a PAID order with insufficient system balance raises BalanceError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product with low system balance
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(30.0)  # Only 30, need 50 (5 * 10)
        await session.commit()
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BalanceError) as exc_info:
        await controller.create_paid_order(order_dto)
    
    assert "Insufficient balance" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_paid_order_with_negative_quantity():
    """Test creating a PAID order with negative quantity raises BadRequestError"""
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
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=-5,
        price_per_unit=10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.create_paid_order(order_dto)
    
    assert "Incorrect parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_paid_order_with_negative_price():
    """Test creating a PAID order with negative price raises BadRequestError"""
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
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=-10.0,
        status=OrderStatus.PAID,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.create_paid_order(order_dto)
    
    assert "Incorrect parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_paid_order_exact_balance():
    """Test creating a PAID order when balance equals exactly the order cost"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product with exact balance
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(50.0)  # Exactly 50 (5 * 10)
        await session.commit()
    
    # Execute
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
    
    # Verify
    assert created_order.status == OrderStatus.PAID
    
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 0.0
