import pytest
from datetime import datetime
from app.repositories.order_repository import OrderRepository
from app.models.order_status import OrderStatus
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository


@pytest.mark.asyncio
async def test_get_order_existing_order():
    """Test retrieving an existing order by ID"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        
        # Setup: Create a product and an order
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        created_order = await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        # Execute
        retrieved_order = await order_repo.get_order(1)
        
        # Assert
        assert retrieved_order is not None
        assert retrieved_order.id == created_order.id
        assert retrieved_order.product_barcode == "5901234123457"
        assert retrieved_order.quantity == 5
        assert retrieved_order.price_per_unit == 10.0
        assert retrieved_order.status == OrderStatus.ISSUED


@pytest.mark.asyncio
async def test_get_order_non_existent_order():
    """Test retrieving a non-existent order returns None"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        
        # Execute
        retrieved_order = await order_repo.get_order(999)
        
        # Assert
        assert retrieved_order is None


@pytest.mark.asyncio
async def test_get_order_multiple_orders():
    """Test retrieving specific order when multiple exist"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        
        # Setup: Create a product
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        # Create multiple orders
        order1 = await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        order2 = await order_repo.create_order(
            id=2,
            product_barcode="5901234123457",
            quantity=3,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        # Execute: Get specific order
        retrieved_order = await order_repo.get_order(2)
        
        # Assert
        assert retrieved_order is not None
        assert retrieved_order.id == 2
        assert retrieved_order.quantity == 3


@pytest.mark.asyncio
async def test_get_order_with_paid_status():
    """Test retrieving an order with PAID status"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product and a PAID order
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        # Initialize system balance
        await system_repo.create_system_info(1000.0)
        
        created_order = await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        
        # Execute
        retrieved_order = await order_repo.get_order(1)
        
        # Assert
        assert retrieved_order is not None
        assert retrieved_order.status == OrderStatus.PAID
