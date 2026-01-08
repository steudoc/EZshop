import pytest
from unittest.mock import MagicMock, AsyncMock
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO

# --- FIXTURES (Standard Setup) ---

@pytest.fixture
def mock_session():
    """
    Creates a mock database session.
    """
    session = MagicMock()
    # Async Context Manager
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    # Async Methods
    session.get = AsyncMock()
    return session

@pytest.fixture
def repository(mock_session):
    """Initializes the repository with the injected mock session."""
    repo = ProductRepository()
    repo._get_session = AsyncMock(return_value=mock_session)
    return repo

# --- TEST CASES ---

@pytest.mark.asyncio
async def test_get_product_by_id_found(repository, mock_session):
    """
    Test that retrieving a product by ID returns the product object if it exists.
    """
    # ARRANGE
    product_id = 1
    expected_product = ProductDAO(id=product_id, barcode="1234567890128", description="Test Prod")
    
    # Configure session.get to return our product
    mock_session.get.return_value = expected_product

    # ACT
    result = await repository.get_product_by_id(product_id)

    # ASSERT
    assert result == expected_product
    assert result.id == product_id
    
    # Verify the database call was made with the correct Model and ID
    mock_session.get.assert_awaited_once_with(ProductDAO, product_id)

@pytest.mark.asyncio
async def test_get_product_by_id_not_found(repository, mock_session):
    """
    Test that retrieving a non-existent product returns None.
    """
    # ARRANGE
    product_id = 999
    
    # Configure session.get to return None (Simulate not found)
    mock_session.get.return_value = None

    # ACT
    result = await repository.get_product_by_id(product_id)

    # ASSERT
    assert result is None
    
    # Verify the database call
    mock_session.get.assert_awaited_once_with(ProductDAO, product_id)