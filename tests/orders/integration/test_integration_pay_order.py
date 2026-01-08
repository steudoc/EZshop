import pytest
from datetime import datetime
from app.controllers.order_controller import OrderController
from app.models.DTO.order_dto import OrderDTO
from app.models.order_status import OrderStatus
from app.models.errors.bad_request import BadRequestError
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.balance_error import BalanceError
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository
from app.repositories.order_repository import OrderRepository


@pytest.mark.asyncio
async def test_pay_order_success():
    """Test successfully paying an ISSUED order"""
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
    
    # Execute: Pay the order
    await controller.pay_order(created_order.id)
    
    # Verify: Check order status changed to PAID
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        updated_order = await order_repo.get_order(created_order.id)
        assert updated_order.status == OrderStatus.PAID
    
    # Verify: Check balance was deducted
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 950.0  # 1000 - (5 * 10)


@pytest.mark.asyncio
async def test_pay_order_not_found():
    """Test paying an order that doesn't exist raises NotFoundError"""
    await reset_db()
    await init_db()
    
    # Execute & Verify
    controller = OrderController()
    
    with pytest.raises(NotFoundError) as exc_info:
        await controller.pay_order(999)
    
    assert "Order not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_pay_order_invalid_id_negative():
    """Test paying with negative order ID raises BadRequestError"""
    await reset_db()
    await init_db()
    
    # Execute & Verify
    controller = OrderController()
    
    with pytest.raises(BadRequestError) as exc_info:
        await controller.pay_order(-1)
    
    assert "Invalid order id" in str(exc_info.value)


@pytest.mark.asyncio
async def test_pay_order_already_paid():
    """Test paying an order that is already PAID raises InvalidStateError"""
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
    
    # Create a PAID order directly
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
    
    # Execute & Verify: Try to pay an already paid order
    with pytest.raises(InvalidStateError) as exc_info:
        await controller.pay_order(created_order.id)
    
    assert "Order was not Issued" in str(exc_info.value)


@pytest.mark.asyncio
async def test_pay_order_insufficient_balance():
    """Test paying an order when system balance is insufficient raises BalanceError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product with initial high balance
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
    
    # Reduce balance to insufficient level
    async with AsyncSessionLocal() as session:
        system_repo = SystemRepository(session)
        await system_repo.create_system_info(30.0)  # Only 30, need 50
        await session.commit()
    
    # Execute & Verify
    with pytest.raises(BalanceError) as exc_info:
        await controller.pay_order(created_order.id)
    
    assert "Insufficient balance" in str(exc_info.value)
