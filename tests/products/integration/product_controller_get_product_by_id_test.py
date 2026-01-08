import asyncio
import pytest
import pytest_asyncio
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
from app.models.DTO.product_dto import ProductDTO
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO

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
async def sample_product():
    """
    Inserts a sample product into the database to be retrieved.
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128",  # Valid EAN-13
            price_per_unit=10.0,
            description="Target Product",
            quantity=50,
            position="1-A-10",        # Valid Position
            note="To be found",
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR GET_PRODUCT_BY_ID ---

@pytest.mark.asyncio
async def test_get_product_by_id_success(sample_product):
    """
    Test that a product is correctly retrieved if the ID exists.
    """
    controller = ProductController()

    # Call the controller using the ID from the fixture
    result = await controller.get_product_by_id(sample_product.id)

    # Assertions
    assert result is not None
    assert isinstance(result, ProductDTO)
    assert result.id == sample_product.id
    assert result.barcode == "1234567890128"
    assert result.description == "Target Product"

@pytest.mark.asyncio
async def test_get_product_by_id_not_found():
    """
    Test that the controller returns None if the ID does not exist.
    """
    controller = ProductController()

    # Use an ID that certainly does not exist (DB is reset before this test)
    non_existent_id = 999999

    result = await controller.get_product_by_id(non_existent_id)

    # Assertions
    assert result is None