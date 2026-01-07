import pytest
import pytest_asyncio
from sqlalchemy import select
from app.database.database import AsyncSessionLocal
from app.controllers.product_controller import ProductController
from app.models.DTO.product_dto import ProductDTO
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.conflict_error import ConflictError
from app.models.errors.bad_request import BadRequestError 

# Helper to get a session within the test
async def _get_session():
    return AsyncSessionLocal()

# --- FIXTURES WITH VALID DATA ---

@pytest_asyncio.fixture
async def existing_product_on_shelf():
    """
    Creates a VALID product in the DB.
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
            note="Pre-existing"
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- CREATE PRODUCT TESTS ---

@pytest.mark.asyncio
async def test_create_product_success():
    """Test successful creation with perfectly valid data"""
    controller = ProductController()
    
    # Valid Barcode (EAN-13 test code with correct checksum)
    # Valid Position (matches digits-letters-digits format)
    valid_dto = ProductDTO(
        barcode="1234567890128", 
        price_per_unit=15.50,
        description="Valid Product",
        quantity=10,
        position="1-B-20", 
        note="Fresh item"
    )

    result = await controller.create_product(valid_dto)

    assert result.barcode == "1234567890128"
    assert result.position == "1-B-20"
    assert result.id is not None

    # Verify actual persistence in DB
    async with await _get_session() as session:
        stmt = select(ProductDAO).where(ProductDAO.barcode == "1234567890128")
        db_result = await session.execute(stmt)
        saved_product = db_result.scalar_one_or_none()
        assert saved_product is not None
        assert saved_product.description == "Valid Product"

@pytest.mark.asyncio
async def test_create_product_invalid_barcode_format():
    """Test failure when barcode is invalid (wrong checksum or length)"""
    controller = ProductController()
    
    # '12345' is too short
    # '1234567890120' has a wrong checksum (should end with 8)
    invalid_dto = ProductDTO(
        barcode="12345", 
        price_per_unit=10.0,
        description="Invalid Barcode",
        position="1-A-1"
    )

    # The controller calls is_product_data_valid, which should return False
    # and trigger a BadRequestError
    with pytest.raises(BadRequestError):
        await controller.create_product(invalid_dto)

@pytest.mark.asyncio
async def test_create_product_invalid_position_format():
    """Test failure when position format does not match regex"""
    controller = ProductController()
    
    # 'A1' does NOT match the regex \d+-\w+-\d+
    invalid_pos_dto = ProductDTO(
        barcode="1234567890128", 
        price_per_unit=10.0,
        description="Bad Position",
        position="A1" 
    )

    with pytest.raises(BadRequestError):
        await controller.create_product(invalid_pos_dto)

@pytest.mark.asyncio
async def test_create_product_defaults_valid():
    """
    Tests default values.
    Position None -> "" (Empty string is considered valid by is_position_valid)
    """
    controller = ProductController()
    
    # Use a different valid barcode
    dto = ProductDTO(
        barcode="5012345678900", 
        price_per_unit=5.0,
        description="Default Values",
        quantity=None, 
        position=None 
    )

    result = await controller.create_product(dto)

    assert result.quantity == 0
    assert result.position == "" # Must be empty string

@pytest.mark.asyncio
async def test_create_product_conflict_position(existing_product_on_shelf):
    """Test conflict when trying to use a valid but occupied position"""
    controller = ProductController()
    
    # Use a NEW valid barcode, but the position of the existing product
    conflict_dto = ProductDTO(
        barcode="9780201379624", # Valid ISBN-13
        price_per_unit=20.0,
        description="Conflict Product",
        quantity=1,
        position="100-A-10" # Same position as the fixture
    )

    with pytest.raises(ConflictError):
        await controller.create_product(conflict_dto)