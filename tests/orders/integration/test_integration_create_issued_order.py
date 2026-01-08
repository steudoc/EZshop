import pytest
from datetime import datetime
from app.controllers.order_controller import OrderController
from app.models.DTO.order_dto import OrderDTO
from app.models.order_status import OrderStatus
from app.models.errors.bad_request import BadRequestError
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository


@pytest.mark.asyncio
async def test_create_issued_order_success():
    """Test successfully creating an ISSUED order"""
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
    
    # Execute
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
    
    # Verify
    assert created_order.id is not None
    assert created_order.product_barcode == "4006381333931"
    assert created_order.quantity == 5
    assert created_order.price_per_unit == 10.0
    assert created_order.status == OrderStatus.ISSUED
    assert created_order.issue_date is not None


@pytest.mark.asyncio
async def test_create_issued_order_with_zero_quantity():
    """Test creating an ISSUED order with zero quantity raises BadRequestError"""
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
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=0,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.create_issued_order(order_dto)
    
    assert "Incorrect parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_issued_order_with_negative_quantity():
    """Test creating an ISSUED order with negative quantity raises BadRequestError"""
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
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=-5,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.create_issued_order(order_dto)
    
    assert "Incorrect parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_issued_order_with_zero_price():
    """Test creating an ISSUED order with zero price raises BadRequestError"""
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
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.create_issued_order(order_dto)
    
    assert "Incorrect parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_issued_order_with_negative_price():
    """Test creating an ISSUED order with negative price raises BadRequestError"""
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
    
    # Execute & Verify
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=5,
        price_per_unit=-10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.create_issued_order(order_dto)
    
    assert "Incorrect parameters" in str(exc_info.value)
