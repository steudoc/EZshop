import pytest
from unittest.mock import MagicMock, AsyncMock
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.bad_request import BadRequestError

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
async def test_is_position_free_yes(repository, mock_session):
    """
    Test that returns True when the position is valid and NOT found in the DB.
    """
    # ARRANGE
    valid_position = "101-A-01"
    
    # Mock database returning None (No product found at this position)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.is_position_free(valid_position)

    # ASSERT
    assert result is True
    
    # Verify DB query was executed
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_is_position_free_no(repository, mock_session):
    """
    Test that returns False when the position is valid but already OCCUPIED in the DB.
    """
    # ARRANGE
    valid_position = "101-A-01"
    existing_product = ProductDAO(id=1, position=valid_position)
    
    # Mock database returning a Product (Position is occupied)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_product
    
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.is_position_free(valid_position)

    # ASSERT
    assert result is False
    
    # Verify DB query was executed
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_position", [
    "INVALID",      # No hyphens
    "123-123",      # Missing letters
    "A-1-A",        # Wrong order
    "123",          # Numbers only

])
async def test_is_position_free_invalid_format(repository, mock_session, invalid_position):
    """
    Test that checking an invalid position format raises BadRequestError
    WITHOUT querying the database.
    """
    # ACT & ASSERT
    with pytest.raises(BadRequestError):
        await repository.is_position_free(invalid_position)
    
    # Critical: Ensure DB was never queried
    mock_session.execute.assert_not_called()