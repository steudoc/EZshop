import pytest
import pytest_asyncio
import asyncio
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError

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
async def stock_product():
    """
    Creates a product with an initial quantity of 50.
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128", 
            price_per_unit=10.0,
            description="Stock Product",
            quantity=50, # Initial Quantity
            position="1-A-10",
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR INCREMENT_PRODUCT_QUANTITY ---

@pytest.mark.asyncio
async def test_increment_quantity_add_success(stock_product):
    """
    Test adding a positive amount to the quantity.
    Start: 50, Increment: +10 -> Result: 60
    """
    controller = ProductController()

    await controller.increment_product_quantity(stock_product.id, 10)

    # Verify update in DB
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, stock_product.id)
        assert updated_product.quantity == 60

@pytest.mark.asyncio
async def test_increment_quantity_subtract_success(stock_product):
    """
    Test removing stock by passing a negative increment.
    Start: 50, Increment: -20 -> Result: 30
    """
    controller = ProductController()

    await controller.increment_product_quantity(stock_product.id, -20)

    # Verify update in DB
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, stock_product.id)
        assert updated_product.quantity == 30

@pytest.mark.asyncio
async def test_increment_quantity_not_found():
    """
    Test that NotFoundError is thrown if the ID does not exist.
    """
    controller = ProductController()
    
    non_existent_id = 999999

    with pytest.raises(NotFoundError):
        await controller.increment_product_quantity(non_existent_id, 10)

@pytest.mark.asyncio
async def test_increment_quantity_bad_request_negative_result(stock_product):
    """
    Test that BadRequestError is thrown if the result would be negative.
    Start: 50, Increment: -60 -> Result: -10 (Invalid)
    """
    controller = ProductController()

    # Try to remove more than what is available
    with pytest.raises(BadRequestError):
        await controller.increment_product_quantity(stock_product.id, -60)

    # Verify DB remains unchanged
    async with await _get_session() as session:
        unchanged_product = await session.get(ProductDAO, stock_product.id)
        assert unchanged_product.quantity == 50