import pytest
import pytest_asyncio
import asyncio
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.conflict_error import ConflictError
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
async def product_to_move():
    """
    Creates a product at position '1-A-10'.
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128", 
            price_per_unit=10.0,
            description="Movable Product",
            quantity=10,
            position="1-A-10",
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

@pytest_asyncio.fixture
async def obstacle_product():
    """
    Creates a product at position '2-B-20' to create a conflict.
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="4006381333931", 
            price_per_unit=5.0,
            description="Obstacle",
            quantity=5,
            position="2-B-20", 
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR MOVE_PRODUCT ---

@pytest.mark.asyncio
async def test_move_product_success(product_to_move):
    """
    Test moving a product from one valid position to another free valid position.
    1-A-10 -> 3-C-30
    """
    controller = ProductController()
    
    new_position = "3-C-30" # Valid and Free

    await controller.move_product(product_to_move.id, new_position)

    # Verify update in DB
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, product_to_move.id)
        assert updated_product.position == new_position

@pytest.mark.asyncio
async def test_move_product_reset_position(product_to_move):
    """
    Test resetting the position (unassigning it) by passing an empty string.
    """
    controller = ProductController()
    
    await controller.move_product(product_to_move.id, "")

    # Verify update in DB
    async with await _get_session() as session:
        updated_product = await session.get(ProductDAO, product_to_move.id)
        assert updated_product.position == ""

@pytest.mark.asyncio
async def test_move_product_not_found():
    """
    Test that NotFoundError is thrown if the ID does not exist.
    """
    controller = ProductController()
    
    non_existent_id = 999999

    with pytest.raises(NotFoundError):
        await controller.move_product(non_existent_id, "1-A-1")

@pytest.mark.asyncio
async def test_move_product_conflict(product_to_move, obstacle_product):
    """
    Test that ConflictError is thrown if the target position is occupied.
    Target: 2-B-20 (Occupied by obstacle_product)
    """
    controller = ProductController()

    with pytest.raises(ConflictError):
        await controller.move_product(product_to_move.id, "2-B-20")

    # Verify the position did NOT change
    async with await _get_session() as session:
        unchanged_product = await session.get(ProductDAO, product_to_move.id)
        assert unchanged_product.position == "1-A-10"

@pytest.mark.asyncio
async def test_move_product_invalid_format(product_to_move):
    """
    Test that BadRequestError is thrown if the new position format is invalid.
    (This assumes repo.is_position_free checks validity and throws BadRequest)
    """
    controller = ProductController()

    # "INVALID" does not match regex \d+-\w+-\d+
    with pytest.raises(BadRequestError):
        await controller.move_product(product_to_move.id, "INVALID_POS")