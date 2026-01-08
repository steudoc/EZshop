import asyncio
import pytest
import pytest_asyncio
from sqlalchemy import select
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
from app.models.DTO.product_dto import ProductDTO
# CRITICAL IMPORT: This ensures the 'products' table is registered in Base.metadata
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.conflict_error import ConflictError
from app.models.errors.bad_request import BadRequestError 

# --- INFRASTRUCTURE FIXTURES (Matches your example) ---

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
def setup_database(event_loop):
    async def _reset():
        await reset_db() # Drop all tables
        await init_db()  # Recreate all tables
    event_loop.run_until_complete(_reset())

async def _get_session() -> AsyncSession:
        return AsyncSessionLocal()

# --- DATA FIXTURES ---

@pytest_asyncio.fixture
async def existing_product_on_shelf():
    """
    Creates a VALID product in the DB to test conflicts.
    Barcode: 4006381333931 (Valid EAN-13)
    Position: 100-A-10 (Matches regex \d+-\w+-\d+)
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="4006381333931",
            price_per_unit=10.0,
            description="Existing Product",
            quantity=5,
            position="100-A-10",
            note="Pre-existing",
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR CREATE PRODUCT ---

@pytest.mark.asyncio
async def test_create_product_success():
    controller = ProductController()
    
    # Valid Barcode (Correct Checksum) and Valid Position (Digit-Char-Digit)
    valid_dto = ProductDTO(
        barcode="1234567890128", 
        price_per_unit=15.50,
        description="Valid Product",
        quantity=10,
        position="1-B-20", 
        note="Fresh item"
    )

    result = await controller.create_product(valid_dto)

    # 1. Check returned DTO
    assert isinstance(result, ProductDTO)
    assert result.barcode == "1234567890128"
    assert result.position == "1-B-20"
    assert result.id is not None 

    # 2. Check Database Persistence
    async with await _get_session() as session:
        stmt = select(ProductDAO).where(ProductDAO.barcode == "1234567890128")
        db_result = await session.execute(stmt)
        saved_product = db_result.scalar_one_or_none()
        
        assert saved_product is not None
        assert saved_product.description == "Valid Product"

@pytest.mark.asyncio
async def test_create_product_defaults_valid():
    """Tests that None values for quantity and position are converted to defaults"""
    controller = ProductController()
    
    dto = ProductDTO(
        barcode="5012345678900", # Valid EAN-13
        price_per_unit=5.0,
        description="Default Values Product",
        quantity=None, # Should become 0
        position=None  # Should become ""
    )

    result = await controller.create_product(dto)

    assert result.quantity == 0
    assert result.position == "" # Empty string is a valid unassigned position

@pytest.mark.asyncio
async def test_create_product_invalid_barcode():
    controller = ProductController()
    
    # Invalid: Too short or wrong checksum
    invalid_dto = ProductDTO(
        barcode="123", 
        price_per_unit=10.0,
        description="Bad Barcode",
        position=""
    )

    with pytest.raises(BadRequestError):
        await controller.create_product(invalid_dto)

@pytest.mark.asyncio
async def test_create_product_invalid_position_format():
    controller = ProductController()
    
    # Invalid: 'A1' does not match format \d+-\w+-\d+
    invalid_pos_dto = ProductDTO(
        barcode="1234567890128", 
        price_per_unit=10.0,
        description="Bad Position",
        position="A1" 
    )

    with pytest.raises(BadRequestError):
        await controller.create_product(invalid_pos_dto)

@pytest.mark.asyncio
async def test_create_product_conflict_position(existing_product_on_shelf):
    """Fails if trying to place a new product in an occupied position"""
    controller = ProductController()
    
    # Valid new barcode, but position is occupied by fixture
    conflict_dto = ProductDTO(
        barcode="9780201379624", 
        price_per_unit=20.0,
        description="Conflict Position",
        quantity=1,
        position="100-A-10" # Same as fixture
    )

    with pytest.raises(ConflictError):
        await controller.create_product(conflict_dto)

@pytest.mark.asyncio
async def test_create_product_conflict_barcode(existing_product_on_shelf):
    """Fails if a product with the same barcode already exists"""
    controller = ProductController()
    
    # Same barcode as fixture
    conflict_dto = ProductDTO(
        barcode="4006381333931", 
        price_per_unit=20.0,
        description="Duplicate Barcode",
        quantity=1,
        position=""
    )

    with pytest.raises(ConflictError):
        await controller.create_product(conflict_dto)