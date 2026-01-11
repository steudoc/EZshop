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

# --- DATA FIXTURES ---

@pytest_asyncio.fixture
async def involved_product():
    """
    Creates a product already involved in 2 operations.
    involvedOperations = 2
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128", 
            price_per_unit=10.0,
            description="Active Product",
            quantity=10,
            position="1-A-10",
            involvedOperations=2 # Starts with 2 active ops
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

@pytest_asyncio.fixture
async def free_product():
    """
    Creates a product NOT involved in any operations.
    involvedOperations = 0
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="4006381333931", 
            price_per_unit=5.0,
            description="Free Product",
            quantity=5,
            position="2-B-20",
            involvedOperations=0 # Not involved
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR EXCLUDE_PRODUCT_FROM_OP ---

@pytest.mark.asyncio
async def test_exclude_product_from_op_success(involved_product):
    """
    Test decrementing the counter successfully.
    Start: 2 -> Exclude -> Result: 1
    """
    controller = ProductController()

    await controller.exclude_product_from_op(involved_product.id)

    # Verify update in DB
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, involved_product.id)
        assert updated_product.involvedOperations == 1

@pytest.mark.asyncio
async def test_exclude_product_from_op_success_to_zero(involved_product):
    """
    Test decrementing until zero.
    Start: 2 -> Exclude twice -> Result: 0
    """
    controller = ProductController()

    await controller.exclude_product_from_op(involved_product.id)
    await controller.exclude_product_from_op(involved_product.id)

    # Verify update in DB
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, involved_product.id)
        assert updated_product.involvedOperations == 0

@pytest.mark.asyncio
async def test_exclude_product_from_op_bad_request(free_product):
    """
    Test that BadRequestError is thrown if involvedOperations is already 0.
    """
    controller = ProductController()

    # The product starts at 0, so removing it should fail
    with pytest.raises(BadRequestError):
        await controller.exclude_product_from_op(free_product.id)
    
    # Verify it remained 0
    async with await _get_session() as session:
        unchanged_product = await session.get(ProductDAO, free_product.id)
        assert unchanged_product.involvedOperations == 0

@pytest.mark.asyncio
async def test_exclude_product_from_op_not_found():
    """
    Test that NotFoundError is thrown if the product ID does not exist.
    """
    controller = ProductController()
    
    non_existent_id = 999999

    with pytest.raises(NotFoundError):
        await controller.exclude_product_from_op(non_existent_id)