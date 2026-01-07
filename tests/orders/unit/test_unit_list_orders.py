import pytest
from datetime import datetime
from app.repositories.order_repository import OrderRepository
from app.models.order_status import OrderStatus
from app.models.DAO.order_dao import OrderDAO
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository


@pytest.mark.asyncio
async def test_list_orders_empty():
    """Test listing orders when no orders exist"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        
        # Execute
        orders = await order_repo.list_orders()
        
        # Assert
        assert orders == []
        assert len(orders) == 0


@pytest.mark.asyncio
async def test_list_orders_single_order():
    """Test listing orders with a single order"""
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
        orders = await order_repo.list_orders()
        
        # Assert
        assert len(orders) == 1
        assert orders[0].id == created_order.id
        assert orders[0].product_barcode == "5901234123457"


@pytest.mark.asyncio
async def test_list_orders_multiple_orders():
    """Test listing orders with multiple orders"""
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
        
        # Execute
        orders = await order_repo.list_orders()
        
        # Assert
        assert len(orders) == 2
        order_ids = [order.id for order in orders]
        assert order1.id in order_ids
        assert order2.id in order_ids


@pytest.mark.asyncio
async def test_list_orders_with_different_statuses():
    """Test listing orders with different statuses"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product
        await product_repo.create_product(
            barcode="5901234123457",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100
        )
        
        # Initialize system balance for PAID order
        await system_repo.create_system_info(1000.0)
        
        # Create orders with different statuses
        await order_repo.create_order(
            id=1,
            product_barcode="5901234123457",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        await order_repo.create_order(
            id=2,
            product_barcode="5901234123457",
            quantity=3,
            price_per_unit=10.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        
        # Execute
        orders = await order_repo.list_orders()
        
        # Assert
        assert len(orders) == 2
        statuses = [order.status for order in orders]
        assert OrderStatus.ISSUED in statuses
        assert OrderStatus.PAID in statuses
