import asyncio
import pytest
import pytest_asyncio
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
from app.models.DTO.product_dto import ProductDTO
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO
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
async def sample_product():
    """
    Inserts a sample product into the database.
    Barcode: 1234567890128 (Valid EAN-13)
    """
    async with await _get_session() as session:
        product = ProductDAO(
            barcode="1234567890128", 
            price_per_unit=10.0,
            description="Barcoded Product",
            quantity=50,
            position="1-A-10",
            note="To be found by barcode",
            involvedOperations=0
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

# --- TEST CASES FOR GET_PRODUCT_BY_BARCODE ---

@pytest.mark.asyncio
async def test_get_product_by_barcode_success(sample_product):
    """
    Test successful retrieval with a valid, existing barcode.
    """
    controller = ProductController()

    result = await controller.get_product_by_barcode(sample_product.barcode)

    assert result is not None
    assert isinstance(result, ProductDTO)
    assert result.barcode == "1234567890128"
    assert result.description == "Barcoded Product"

@pytest.mark.asyncio
async def test_get_product_by_barcode_not_found():
    """
    Test that searching for a VALID barcode that doesn't exist returns None.
    Note: We must use a valid EAN-13 to avoid BadRequestError.
    """
    controller = ProductController()

    # "4006381333931" is a valid EAN-13 barcode, but it's not in the DB.
    valid_but_missing_barcode = "4006381333931"

    result = await controller.get_product_by_barcode(valid_but_missing_barcode)

    assert result is None

@pytest.mark.asyncio
async def test_get_product_by_barcode_invalid_format():
    """
    Test that searching with an INVALID barcode throws BadRequestError.
    (e.g., wrong length, letters, or wrong checksum)
    """
    controller = ProductController()

    # "123" is too short (invalid format)
    # "ABC" contains letters (invalid format)
    invalid_barcodes = ["123", "ABC", "1234567890120"] # Last one has wrong checksum

    for b_code in invalid_barcodes:
        with pytest.raises(BadRequestError):
            await controller.get_product_by_barcode(b_code)