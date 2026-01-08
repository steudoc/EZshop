import pytest
from datetime import datetime
from app.repositories.order_repository import OrderRepository
from app.models.order_status import OrderStatus
from app.models.DAO.order_dao import OrderDAO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.balance_error import BalanceError
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository


@pytest.mark.asyncio
async def test_create_order_success():
    """Test successfully creating an order with ISSUED status"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        
        # Setup: Create a product with valid barcode (GTIN-13)
        product = await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        # Execute: Create order with ISSUED status
        order = await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        # Assert
        assert order is not None
        assert order.id == 1
        assert order.product_barcode == "5901234123457"
        assert order.quantity == 5
        assert order.price_per_unit == 10.0
        assert order.status == OrderStatus.ISSUED


@pytest.mark.asyncio
async def test_create_order_paid_with_sufficient_balance():
    """Test creating an order with PAID status when balance is sufficient"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product and ensure system has balance
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        # Set up sufficient balance
        await system_repo.create_system_info(1000.0)
        
        # Execute: Create order with PAID status
        order = await order_repo.create_order(
            id=2,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        
        # Assert
        assert order is not None
        assert order.status == OrderStatus.PAID
        
        # Verify balance was deducted
        system_info = await system_repo.get_last_system_info()
        assert system_info.balance == 950.0  # 1000 - (5 * 10)


@pytest.mark.asyncio
async def test_create_order_product_not_found():
    """Test creating an order with non-existent product raises NotFoundError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await order_repo.create_order(
                id=3,
                product_barcode="5901234123457",
                quantity=5,
                price_per_unit=10.0,
                status=OrderStatus.ISSUED,
                issue_date=datetime.now()
            )
        
        assert "Product not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_order_insufficient_balance():
    """Test creating an order with PAID status when balance is insufficient raises BalanceError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product and set insufficient balance
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        # Set insufficient balance
        await system_repo.create_system_info(30.0)  # Only 30, need 50 (5 * 10)
        
        # Execute & Assert
        with pytest.raises(BalanceError) as exc_info:
            await order_repo.create_order(
                id=4,
                product_barcode="5901234123457",
                quantity=5,
                price_per_unit=10.0,
                status=OrderStatus.PAID,
                issue_date=datetime.now()
            )
        
        assert "Insufficient balance" in str(exc_info.value)
