import pytest
from datetime import datetime
from app.repositories.order_repository import OrderRepository
from app.models.order_status import OrderStatus
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.balance_error import BalanceError
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository


@pytest.mark.asyncio
async def test_update_issued_order_success():
    """Test successfully updating an ISSUED order to PAID status"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product and sufficient balance
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        await system_repo.create_system_info(1000.0)
        
        # Create an ISSUED order
        order = await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        # Execute
        updated_order = await order_repo.update_issued_order(1)
        
        # Assert
        assert updated_order is not None
        assert updated_order.id == 1
        assert updated_order.status == OrderStatus.PAID
        
        # Verify balance was deducted
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 950.0  # 1000 - (5 * 10)


@pytest.mark.asyncio
async def test_update_issued_order_not_found():
    """Test updating non-existent order raises NotFoundError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await order_repo.update_issued_order(999)
        
        assert "Order not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_issued_order_invalid_state_paid():
    """Test updating an order that is not ISSUED status raises InvalidStateError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create product and order with PAID status
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        await system_repo.create_system_info(1000.0)
        
        # Create a PAID order directly
        await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        
        # Execute & Assert
        with pytest.raises(InvalidStateError) as exc_info:
            await order_repo.update_issued_order(1)
        
        assert "Order was not Issued" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_issued_order_insufficient_balance():
    """Test updating order when balance is insufficient raises BalanceError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create product and minimal balance
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        # Set insufficient balance (need 50, have only 30)
        await system_repo.create_system_info(30.0)
        
        # Create an ISSUED order
        await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        # Execute & Assert
        with pytest.raises(BalanceError) as exc_info:
            await order_repo.update_issued_order(1)
        
        assert "Insufficient balance" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_issued_order_completed_status():
    """Test updating an order that is COMPLETED status raises InvalidStateError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create product and necessary balance
        product = await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            position="1-A-1"
        )
        
        await system_repo.create_system_info(1000.0)
        
        # Create and progress order to COMPLETED
        order = await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        # Transition to PAID
        await order_repo.update_issued_order(1)
        
        # Transition to COMPLETED
        await order_repo.update_paid_order(1)
        
        # Execute & Assert - Try to update COMPLETED order
        with pytest.raises(InvalidStateError):
            await order_repo.update_issued_order(1)
