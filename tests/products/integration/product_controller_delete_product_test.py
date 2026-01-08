import pytest
import pytest_asyncio
import asyncio

from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError

# --- INFRASTRUCTURE FIXTURES ---

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
def setup_database(event_loop):
    async def _reset():
        await reset_db()
        await init_db()
    event_loop.run_until_complete(_reset())

async def _get_session() -> AsyncSession:
    return AsyncSessionLocal()

# --- DATA FIXTURES ---

@pytest_asyncio.fixture
async def deletable_product():
    """
    Creates a product that can be safely deleted (involvedOperations = 0).
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128", 
            price_per_unit=10.0,
            description="To be deleted",
            quantity=10,
            position="1-A-10",
            involvedOperations=0 # Safe to delete
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

@pytest_asyncio.fixture
async def locked_product():
    """
    Creates a product that is involved in a transaction (involvedOperations > 0).
    Deleting this should raise InvalidStateError.
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="4006381333931", 
            price_per_unit=20.0,
            description="Locked Product",
            quantity=5,
            position="2-B-20",
            involvedOperations=1 # Simulates being in a transaction
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR DELETE_PRODUCT ---

@pytest.mark.asyncio
async def test_delete_product_success(deletable_product):
    """
    Test that a valid, unused product is successfully deleted from the DB.
    """
    controller = ProductController()

    # 1. Execute delete
    await controller.delete_product(deletable_product.id)

    # 2. Verify it is gone from DB
    async with await _get_session() as session:
        # Try to fetch the product by ID
        result = await session.get(ProductDAO, deletable_product.id)
        assert result is None

@pytest.mark.asyncio
async def test_delete_product_not_found():
    """
    Test that deleting a non-existent ID throws NotFoundError.
    """
    controller = ProductController()

    non_existent_id = 999999

    with pytest.raises(NotFoundError):
        await controller.delete_product(non_existent_id)

@pytest.mark.asyncio
async def test_delete_product_invalid_state(locked_product):
    """
    Test that deleting a product involved in operations throws InvalidStateError.
    """
    controller = ProductController()

    # The fixture 'locked_product' has involvedOperations=1
    with pytest.raises(InvalidStateError):
        await controller.delete_product(locked_product.id)

    # Verify it was NOT deleted
    async with await _get_session() as session:
        result = await session.get(ProductDAO, locked_product.id)
        assert result is not None