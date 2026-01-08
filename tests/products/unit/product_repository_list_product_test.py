import pytest
from unittest.mock import MagicMock, AsyncMock
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO

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
    
    # Synchronous methods
    session.add = MagicMock()
    
    return session

@pytest.fixture
def repository(mock_session):
    """
    Initializes the repository with the mocked session injected.
    """
    repo = ProductRepository()
    
    # Inject the mock session by overriding the internal helper method
    repo._get_session = AsyncMock(return_value=mock_session)
    
    return repo

# --- TEST CASES ---

@pytest.mark.asyncio
async def test_list_products_populated(repository, mock_session):
    """
    Test that a list of products is returned when the database is populated.
    """
    # ARRANGE
    # Create dummy products
    prod1 = ProductDAO(id=1, barcode="123456789012", description="Prod 1")
    prod2 = ProductDAO(id=2, barcode="123456789013", description="Prod 2")
    expected_list = [prod1, prod2]

    # Mock the SQLAlchemy chain: result.scalars().all()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = expected_list
    
    # Attach the result to the session execution
    mock_session.execute.return_value = mock_result

    # ACT
    products = await repository.list_products()

    # ASSERT
    assert len(products) == 2
    assert products[0].barcode == "123456789012"
    assert products == expected_list
    
    # Verify the database was queried
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_list_products_empty(repository, mock_session):
    """
    Test that an empty list (and not None) is returned when the database is empty.
    """
    # ARRANGE
    mock_result = MagicMock()
    # The DB returns an empty list
    mock_result.scalars.return_value.all.return_value = []
    
    mock_session.execute.return_value = mock_result

    # ACT
    products = await repository.list_products()

    # ASSERT
    assert isinstance(products, list)
    assert len(products) == 0
    assert products == []
    
    mock_session.execute.assert_called_once()

