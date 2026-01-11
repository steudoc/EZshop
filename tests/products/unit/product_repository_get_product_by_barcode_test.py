import pytest
from unittest.mock import MagicMock, AsyncMock
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.bad_request import BadRequestError

# --- CONSTANTS ---
VALID_BARCODE = "1234567890128" # Valid GTIN-13

# --- FIXTURES ---

@pytest.fixture
def mock_session():
    """Creates a mock database session."""
    session = MagicMock()
    
    # Async Context Manager
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    # Async Methods
    session.execute = AsyncMock()
    
    return session

@pytest.fixture
def repository(mock_session):
    """Initializes the repository with the injected mock session."""
    repo = ProductRepository()
    repo._get_session = AsyncMock(return_value=mock_session)
    return repo

# --- TEST CASES ---

@pytest.mark.asyncio
async def test_get_product_by_barcode_found(repository, mock_session):
    """
    Test that retrieving a product by a valid barcode returns the product object.
    """
    # ARRANGE
    expected_product = ProductDAO(id=1, barcode=VALID_BARCODE, description="Test Prod")
    
    # Mock the chain: session.execute(...) -> result.scalars().first()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = expected_product
    
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.get_product_by_barcode(VALID_BARCODE)

    # ASSERT
    assert result == expected_product
    assert result.barcode == VALID_BARCODE
    
    # Verify DB interaction
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_product_by_barcode_not_found(repository, mock_session):
    """
    Test that retrieving a product that does not exist returns None.
    """
    # ARRANGE
    # Mock the chain to return None
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.get_product_by_barcode(VALID_BARCODE)

    # ASSERT
    assert result is None
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_barcode", [
    "123",              # Too short
    "123456789012345",  # Too long
    "123456789012A",    # Alphanumeric
    "1234567890129",    # Invalid GTIN Checksum (should be 8)
    "",                 # Empty
    None                # None
])
async def test_get_product_by_barcode_invalid_format(repository, mock_session, invalid_barcode):
    """
    Test that an invalid barcode format raises BadRequestError immediately,
    without querying the database.
    """
    # ACT & ASSERT
    with pytest.raises(BadRequestError):
        await repository.get_product_by_barcode(invalid_barcode)
    
    # Verify that the database was NEVER queried
    mock_session.execute.assert_not_called()