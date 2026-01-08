import pytest
import pytest_asyncio
import asyncio
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
from app.models.DTO.product_dto import ProductDTO
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.conflict_error import ConflictError
from app.models.errors.bad_request import BadRequestError
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

# --- DATA FIXTURES ---

@pytest_asyncio.fixture
async def product_to_update():
    """
    Creates a base product to be updated.
    ID: Will be auto-generated
    Barcode: 1234567890128
    Position: 1-A-10
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128", 
            price_per_unit=10.0,
            description="Original Description",
            quantity=10,
            position="1-A-10",
            note="Original Note",
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

@pytest_asyncio.fixture
async def obstacle_product():
    """
    Creates a second product to act as an obstacle for position changes.
    Position: 2-B-20
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="4006381333931", 
            price_per_unit=5.0,
            description="Obstacle",
            quantity=5,
            position="2-B-20", # This position is occupied
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR UPDATE_PRODUCT ---

@pytest.mark.asyncio
async def test_update_product_success(product_to_update):
    """
    Test standard update of description, price, and quantity.
    Position remains unchanged.
    """
    controller = ProductController()
    
    # DTO with updated values
    update_dto = ProductDTO(
        id=product_to_update.id,
        barcode=product_to_update.barcode,
        price_per_unit=50.0,             # Changed
        description="Updated Description", # Changed
        quantity=20,                     # Changed
        position=product_to_update.position,
        note="Updated Note"
    )

    result = await controller.update_product(update_dto)

    # Check returned object
    assert result.description == "Updated Description"
    assert result.price_per_unit == 50.0
    assert result.quantity == 20
    
    # Verify in DB
    async with await _get_session() as session:
        updated_dao = await session.get(ProductDAO, product_to_update.id)
        assert updated_dao.description == "Updated Description"

@pytest.mark.asyncio
async def test_update_product_move_position_success(product_to_update):
    """
    Test successfully moving a product to a new, free position.
    """
    controller = ProductController()
    
    # Move from 1-A-10 to 3-C-30 (Free position)
    update_dto = ProductDTO(
        id=product_to_update.id,
        barcode=product_to_update.barcode,
        price_per_unit=product_to_update.price_per_unit,
        description=product_to_update.description,
        quantity=product_to_update.quantity,
        position="3-C-30", 
        note=product_to_update.note
    )

    result = await controller.update_product(update_dto)

    assert result.position == "3-C-30"

    async with await _get_session() as session:
        updated_dao = await session.get(ProductDAO, product_to_update.id)
        assert updated_dao.position == "3-C-30"

@pytest.mark.asyncio
async def test_update_product_reset_position(product_to_update):
    """
    Test resetting the position to empty string (removing from shelf).
    """
    controller = ProductController()
    
    update_dto = ProductDTO(
        id=product_to_update.id,
        barcode=product_to_update.barcode,
        position="" # Reset position
    )

    result = await controller.update_product(update_dto)

    assert result.position == ""

@pytest.mark.asyncio
async def test_update_product_not_found():
    """
    Test that updating a non-existent ID throws NotFoundError.
    """
    controller = ProductController()
    
    non_existent_id = 99999
    
    update_dto = ProductDTO(
        id=non_existent_id,
        barcode="1234567890128",
        position=""
    )

    with pytest.raises(NotFoundError):
        await controller.update_product(update_dto)

@pytest.mark.asyncio
async def test_update_product_conflict_position(product_to_update, obstacle_product):
    """
    Test that ConflictError is thrown when trying to move to an occupied position.
    """
    controller = ProductController()
    
    # Try to move 'product_to_update' to 'obstacle_product's position
    update_dto = ProductDTO(
        id=product_to_update.id,
        barcode=product_to_update.barcode,
        position="2-B-20" # Occupied by obstacle_product
    )

    with pytest.raises(ConflictError):
        await controller.update_product(update_dto)

@pytest.mark.asyncio
async def test_update_product_bad_request_quantity(product_to_update):
    """
    Test that BadRequestError is thrown if quantity is negative.
    """
    controller = ProductController()
    
    update_dto = ProductDTO(
        id=product_to_update.id,
        barcode=product_to_update.barcode,
        quantity=-10 # Invalid
    )

    with pytest.raises(BadRequestError):
        await controller.update_product(update_dto)