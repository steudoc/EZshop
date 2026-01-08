import pytest
from datetime import datetime
from app.controllers.order_controller import OrderController
from app.models.DTO.order_dto import OrderDTO
from app.models.order_status import OrderStatus
from app.models.errors.bad_request import BadRequestError
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.general_error import GeneralError
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository
from app.repositories.order_repository import OrderRepository


@pytest.mark.asyncio
async def test_complete_order_success():
    """Test successfully completing a PAID order"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product with position and system balance
        product = await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        initial_quantity = product.quantity
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Create an ISSUED order and transition to PAID
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
    
    # Execute: Complete the order
    await controller.complete_order(created_order.id)
    
    # Verify: Check order status changed to COMPLETED
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        updated_order = await order_repo.get_order(created_order.id)
        assert updated_order.status == OrderStatus.COMPLETED
    
    # Verify: Check product quantity was increased
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        updated_product = await product_repo.get_product_by_barcode("4006381333931")
        assert updated_product.quantity == initial_quantity + 5


@pytest.mark.asyncio
async def test_complete_order_not_found():
    """Test completing an order that doesn't exist raises NotFoundError"""
    await reset_db()
    await init_db()
    
    # Execute & Verify
    controller = OrderController()
    
    with pytest.raises(NotFoundError) as exc_info:
        await controller.complete_order(999)
    
    assert "Order not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_complete_order_invalid_id_negative():
    """Test completing with negative order ID raises BadRequestError"""
    await reset_db()
    await init_db()
    
    # Execute & Verify
    controller = OrderController()
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.complete_order(-1)
    
    assert "Invalid order id" in str(exc_info.value)


@pytest.mark.asyncio
async def test_complete_order_issued_status():
    """Test completing an ISSUED order (not PAID) raises InvalidStateError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        
        # Setup: Create a product with position
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        await session.commit()
    
    # Create an ISSUED order
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
    
    # Execute & Verify: Try to complete an ISSUED order
    with pytest.raises(InvalidStateError) as exc_info:
        await controller.complete_order(created_order.id)
    
    assert "Order was not Issued" in str(exc_info.value)


@pytest.mark.asyncio
async def test_complete_order_product_not_found():
    """Test completing an order when the product is missing raises NotFoundError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product with position and system balance
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
    
    # Create and pay an order
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
    
    # Delete the product to simulate missing product
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        product = await product_repo.get_product_by_barcode("4006381333931")
        await session.delete(product)
        await session.commit()
    
    # Execute & Verify
    with pytest.raises(NotFoundError) as exc_info:
        await controller.complete_order(created_order.id)
    
    assert "Product not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_complete_order_no_position():
    """Test completing an order when product has no position raises GeneralError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product WITHOUT position
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position=None  # No position
        )
        
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Create and pay an order
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
    
    # Execute & Verify
    with pytest.raises(GeneralError) as exc_info:
        await controller.complete_order(created_order.id)
    
    assert "Position must be set" in str(exc_info.value)


@pytest.mark.asyncio
async def test_complete_order_restocks_product():
    """Test completing an order properly restocks the product inventory"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product with initial quantity
        product = await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=50,
            note="Test product",
            position="1-A-1"
        )
        
        initial_quantity = product.quantity
        await system_repo.create_system_info(1000.0)
        await session.commit()
    
    # Create and pay an order
    controller = OrderController()
    order_dto = OrderDTO(
        id=None,
        product_barcode="4006381333931",
        quantity=20,
        price_per_unit=10.0,
        status=OrderStatus.ISSUED,
        issue_date=datetime.now()
    )
    
    created_order = await controller.create_issued_order(order_dto)
    await controller.pay_order(created_order.id)
    
    # Execute: Complete the order
    await controller.complete_order(created_order.id)
    
    # Verify: Check product quantity increased by order quantity
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        updated_product = await product_repo.get_product_by_barcode("4006381333931")
        assert updated_product.quantity == initial_quantity + 20
