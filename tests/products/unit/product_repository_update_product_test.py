import pytest
from unittest.mock import MagicMock, AsyncMock
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.bad_request import BadRequestError
from app.models.errors.conflict_error import ConflictError
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError

# --- CONSTANTS (Valid GTIN-13 Barcodes) ---
VALID_BARCODE_OLD = "1234567890128"
VALID_BARCODE_NEW = "9876543210982"

# --- FIXTURES (Setup) ---

@pytest.fixture
def mock_session():
    """
    Creates a mock database session handling both async context managers
    and standard SQLAlchemy methods.
    """
    session = MagicMock()
    
    # Async Context Manager (async with session:)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    # Async Methods
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    
    return session

@pytest.fixture
def repository(mock_session):
    """Initializes the repository with the injected mock session."""
    repo = ProductRepository()
    repo._get_session = AsyncMock(return_value=mock_session)
    return repo

# --- TEST CASES: VALIDATION ---

@pytest.mark.asyncio
@pytest.mark.parametrize("field, invalid_value", [
    ("barcode", "123"),              # Too short
    ("barcode", "123456789012A"),    # Letters
    ("barcode", "1234567890129"),    # Invalid Checksum
    ("price_per_unit", -10.0),       # Negative Price
    ("quantity", -1),                # Negative Quantity
    ("position", "INVALID-FORMAT"),  # Wrong Regex
])
async def test_update_product_invalid_data(repository, mock_session, field, invalid_value):
    """
    Test that invalid data raises BadRequestError immediately.
    """
    # ARRANGE: Create a valid product first
    product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_OLD, 
        description="Valid", 
        price_per_unit=10, 
        quantity=1, 
        position="1-A-1"
    )
    
    # Inject the invalid value
    setattr(product, field, invalid_value)

    # ACT & ASSERT
    with pytest.raises(BadRequestError):
        await repository.update_product(product)
    
    # Ensure DB was never touched
    mock_session.get.assert_not_called()

# --- TEST CASES: HAPPY PATH (Simple Fields) ---

@pytest.mark.asyncio
@pytest.mark.parametrize("field, new_value", [
    ("description", "Updated Name"),
    ("price_per_unit", 99.99),
    ("quantity", 100),
    ("note", "New Note"),
    ("position", "10-B-05"),
])
async def test_update_product_simple_fields(repository, mock_session, field, new_value):
    """
    Test updating fields that are NOT the barcode.
    """
    # ARRANGE
    input_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_OLD, 
        description="Old", 
        price_per_unit=10, 
        quantity=1, 
        position="1-A-1"
    )
    
    db_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_OLD, 
        description="Old", 
        price_per_unit=10, 
        quantity=1, 
        position="1-A-1", 
        involvedOperations=0
    )
    
    # Apply change
    setattr(input_product, field, new_value)
    
    mock_session.get.return_value = db_product

    # Mock the internal check query (empty list = no issues)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.update_product(input_product)

    # ASSERT
    assert getattr(result, field) == new_value
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(db_product)

# --- TEST CASES: COMPLEX LOGIC (Barcode, Conflicts, State) ---

@pytest.mark.asyncio
async def test_update_product_not_found(repository, mock_session):
    """Test update fails if ID does not exist."""
    input_product = ProductDAO(
        id=999, 
        barcode=VALID_BARCODE_OLD, 
        description="Ghost", 
        price_per_unit=10, 
        quantity=1
    )
    mock_session.get.return_value = None # Not Found

    with pytest.raises(NotFoundError):
        await repository.update_product(input_product)

@pytest.mark.asyncio
async def test_update_barcode_success(repository, mock_session):
    """Test successfully changing the barcode (No conflicts, Valid state)."""
    # ARRANGE
    input_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_NEW, 
        description="Fix", 
        price_per_unit=10, 
        quantity=1
    )
    
    db_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_OLD, 
        involvedOperations=0
    ) # Free state
    
    mock_session.get.return_value = db_product

    # Mock conflict check -> No existing product found
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [] 
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.update_product(input_product)

    # ASSERT
    assert result.barcode == VALID_BARCODE_NEW
    mock_session.flush.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_barcode_conflict(repository, mock_session):
    """Test changing barcode fails if new barcode is already taken."""
    # ARRANGE
    input_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_NEW, 
        description="Fix", 
        price_per_unit=10, 
        quantity=1
    )
    
    db_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_OLD, 
        involvedOperations=0
    )
    
    mock_session.get.return_value = db_product

    # Mock conflict check -> Found another product!
    existing_other_product = ProductDAO(id=2, barcode=VALID_BARCODE_NEW)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [existing_other_product]
    mock_session.execute.return_value = mock_result

    # ACT & ASSERT
    with pytest.raises(ConflictError):
        await repository.update_product(input_product)
    
    mock_session.flush.assert_not_called()

@pytest.mark.asyncio
async def test_update_barcode_invalid_state(repository, mock_session):
    """Test changing barcode fails if product is involved in operations."""
    # ARRANGE
    input_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_NEW, 
        description="Fix", 
        price_per_unit=10, 
        quantity=1
    )
    
    # Product is BUSY (involvedOperations > 0)
    db_product = ProductDAO(
        id=1, 
        barcode=VALID_BARCODE_OLD, 
        involvedOperations=5
    )
    
    mock_session.get.return_value = db_product

    # Mock execute to avoid AttributeError (result doesn't matter here)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    # ACT & ASSERT
    with pytest.raises(InvalidStateError):
        await repository.update_product(input_product)
    
    mock_session.flush.assert_not_called()