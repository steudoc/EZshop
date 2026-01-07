import pytest
from unittest.mock import MagicMock, AsyncMock
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.bad_request import BadRequestError
from app.models.errors.conflict_error import ConflictError

# --- CONSTANTS ---
VALID_BARCODE = "1234567890128"  # Valid GTIN-13
VALID_POSITION = "101-A-01"      # Valid Regex format (\d+-\w+-\d+)

# --- FIXTURES ---

@pytest.fixture
def mock_session():
    """
    Creates a mock database session to simulate SQLAlchemy behavior.
    """
    session = MagicMock()
    
    # Handle Async Context Manager (async with session:)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    # Async methods
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    
    # Synchronous methods
    session.add = MagicMock()
    
    return session

@pytest.fixture
def repository(mock_session):
    """
    Initializes the repository with the mocked session injected.
    """
    repo = ProductRepository()
    repo._get_session = AsyncMock(return_value=mock_session)
    
    # Mock the internal helper method to ensure it doesn't block the flow
    # before we reach the actual database transaction logic.
    repo.get_product_by_barcode = AsyncMock(return_value=None)
    
    return repo

# --- PARAMETRIZED VALIDATION TEST ---

@pytest.mark.asyncio
@pytest.mark.parametrize("barcode, price, description, quantity, position, case_desc", [
    # --- BARCODE FAILURES ---
    ("123", 10.0, "Desc", 10, None, "Barcode too short"),
    ("123456789012345", 10.0, "Desc", 10, None, "Barcode too long"),
    ("123456789012A", 10.0, "Desc", 10, None, "Barcode alphanumeric"),
    ("1234567890129", 10.0, "Desc", 10, None, "Barcode invalid checksum"), # Ends in 9 instead of 8
    (None, 10.0, "Desc", 10, None, "Barcode None"),
    ("", 10.0, "Desc", 10, None, "Barcode Empty"),

    # --- DESCRIPTION FAILURES ---
    (VALID_BARCODE, 10.0, None, 10, None, "Description None"),
    (VALID_BARCODE, 10.0, "", 10, None, "Description Empty"),

    # --- PRICE FAILURES ---
    (VALID_BARCODE, -5.0, "Desc", 10, None, "Price Negative"),
    (VALID_BARCODE, None, "Desc", 10, None, "Price None"),

    # --- QUANTITY FAILURES ---
    (VALID_BARCODE, 10.0, "Desc", -1, None, "Quantity Negative"),
    (VALID_BARCODE, 10.0, "Desc", None, None, "Quantity None"),

    # --- POSITION FAILURES ---
    (VALID_BARCODE, 10.0, "Desc", 10, "INVALID", "Position Wrong Format"),
    (VALID_BARCODE, 10.0, "Desc", 10, "123-123", "Position Missing Letters"),
])
async def test_create_product_validation_errors(
    repository, mock_session, barcode, price, description, quantity, position, case_desc
):
    """
    Parametrized test covering ALL validation failure scenarios.
    Ensures BadRequestError is raised and DB is not touched.
    """
    # ACT & ASSERT
    with pytest.raises(BadRequestError):
        await repository.create_product(
            barcode=barcode,
            price_per_unit=price,
            description=description,
            quantity=quantity,
            position=position
        )
    
    # Critical Check: The database should never be touched if validation fails
    mock_session.add.assert_not_called()
    mock_session.flush.assert_not_called()


# --- LOGIC TESTS (Success & Conflict) ---

@pytest.mark.asyncio
async def test_create_product_success(repository, mock_session):
    """
    Test successful product creation (Happy Path).
    """
    # ARRANGE
    # Simulate that the query returns an EMPTY list (No duplicates found)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.create_product(
        barcode=VALID_BARCODE, 
        price_per_unit=10.50, 
        description="New Product", 
        quantity=50, 
        position=VALID_POSITION
    )

    # ASSERT
    assert result.barcode == VALID_BARCODE
    assert result.position == VALID_POSITION
    
    # Verify DB interactions
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_product_conflict(repository, mock_session):
    """
    Test that ConflictError is raised if the product already exists in the DB.
    """
    # ARRANGE
    existing_product = ProductDAO(barcode=VALID_BARCODE)
    
    # Simulate that the query returns a list containing the existing product
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [existing_product]
    mock_session.execute.return_value = mock_result

    # ACT & ASSERT
    with pytest.raises(ConflictError) as excinfo:
        await repository.create_product(VALID_BARCODE, 10.0, "Desc", 5)
        
    assert f"Product with barcode'{VALID_BARCODE}' already exists" in str(excinfo.value)
    
    # Ensure no insertion happened
    mock_session.add.assert_not_called()