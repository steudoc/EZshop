import pytest
import pytest_asyncio
import asyncio
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.notfound_error import NotFoundError

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

# --- DATA FIXTURE ---

@pytest_asyncio.fixture
async def clean_product():
    """
    Creates a product not involved in any operation (involvedOperations=0).
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128", 
            price_per_unit=10.0,
            description="Clean Product",
            quantity=10,
            position="1-A-10",
            involvedOperations=0 # Start at 0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR INCLUDE_PRODUCT_IN_OP ---

@pytest.mark.asyncio
async def test_include_product_in_op_success(clean_product):
    """
    Test that involvedOperations is incremented (0 -> 1).
    """
    controller = ProductController()

    # Action: Include product in an operation
    await controller.include_product_in_op(clean_product.id)

    # Verification: Check DB for the update
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, clean_product.id)
        assert updated_product.involvedOperations == 1

@pytest.mark.asyncio
async def test_include_product_in_op_multiple_times(clean_product):
    """
    Test that calling it multiple times increments the counter correctly (0 -> 2).
    """
    controller = ProductController()

    # Call twice
    await controller.include_product_in_op(clean_product.id)
    await controller.include_product_in_op(clean_product.id)

    # Verification
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, clean_product.id)
        assert updated_product.involvedOperations == 2

@pytest.mark.asyncio
async def test_include_product_in_op_not_found():
    """
    Test that NotFoundError is thrown if the product ID does not exist.
    """
    controller = ProductController()
    
    non_existent_id = 999999

    with pytest.raises(NotFoundError):
        await controller.include_product_in_op(non_existent_id)