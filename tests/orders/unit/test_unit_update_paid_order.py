import pytest
from datetime import datetime
from app.repositories.order_repository import OrderRepository
from app.models.order_status import OrderStatus
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.general_error import GeneralError
from app.database.database import AsyncSessionLocal, init_db, reset_db
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository


@pytest.mark.asyncio
async def test_update_paid_order_success():
    """Test successfully updating a PAID order to COMPLETED status"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product with a position
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
        
        # Create an ISSUED order and transition to PAID
        await order_repo.create_order(
            id=1,
            product_barcode="4006381333931",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        await order_repo.update_issued_order(1)
        
        # Execute
        updated_order = await order_repo.update_paid_order(1)
        
        # Assert
        assert updated_order is not None
        assert updated_order.id == 1
        assert updated_order.status == OrderStatus.COMPLETED
        
        # Verify product quantity was increased
        updated_product = await product_repo.get_product_by_barcode("4006381333931")
        assert updated_product.quantity == initial_quantity + 5


@pytest.mark.asyncio
async def test_update_paid_order_not_found():
    """Test updating non-existent order raises NotFoundError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await order_repo.update_paid_order(999)
        
        assert "Order not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_paid_order_invalid_state_issued():
    """Test updating an ISSUED order raises InvalidStateError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        
        # Setup: Create product and ISSUED order
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product"
        )
        
        await order_repo.create_order(
            id=1,
            product_barcode="4006381333931",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        # Execute & Assert
        with pytest.raises(InvalidStateError) as exc_info:
            await order_repo.update_paid_order(1)
        
        assert "Order was not Issued" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_paid_order_product_not_found():
    """Test updating order when product no longer exists raises NotFoundError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create a product, then delete it before completion
        product = await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(1000.0)
        
        # Create order and progress to PAID
        await order_repo.create_order(
            id=1,
            product_barcode="4006381333931",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        await order_repo.update_issued_order(1)
        
        # Remove product from operation before deleting
        await product_repo.include_product_in_op(product.id, False)
        
        # Delete the product
        await product_repo.delete_product(product.id)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await order_repo.update_paid_order(1)
        
        assert "Product not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_paid_order_no_position():
    """Test updating order when product has no valid position raises GeneralError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create product without position
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product"
            # No position specified
        )
        
        await system_repo.create_system_info(1000.0)
        
        # Create order and progress to PAID
        await order_repo.create_order(
            id=1,
            product_barcode="4006381333931",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        await order_repo.update_issued_order(1)
        
        # Execute & Assert
        with pytest.raises(GeneralError) as exc_info:
            await order_repo.update_paid_order(1)
        
        assert "Position must be set" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_paid_order_multiple_times():
    """Test that attempting to update COMPLETED order raises InvalidStateError"""
    await reset_db()
    await init_db()
    
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        system_repo = SystemRepository(session)
        
        # Setup: Create product with position
        await product_repo.create_product(
            barcode="4006381333931",
            description="Test Product",
            price_per_unit=10.0,
            quantity=100,
            note="Test product",
            position="1-A-1"
        )
        
        await system_repo.create_system_info(1000.0)
        
        # Create order and progress to COMPLETED
        await order_repo.create_order(
            id=1,
            product_barcode="4006381333931",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        
        await order_repo.update_issued_order(1)
        await order_repo.update_paid_order(1)
        
        # Execute & Assert - Try to update COMPLETED order again
        with pytest.raises(InvalidStateError):
            await order_repo.update_paid_order(1)
