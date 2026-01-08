from app.repositories.product_repository import ProductRepository
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.DAO.product_dao import ProductDAO

@pytest.fixture
def mock_session():
    """Creates a mock database session with async support for all used methods."""
    session = MagicMock()
    # Async Context Manager
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    # Async Methods - MUST be AsyncMock because they are 'awaited' in the repo
    session.get = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    return session

@pytest.fixture
def repository(mock_session):
    """Initializes the repository with the injected mock session."""
    repo = ProductRepository()
    repo._get_session = AsyncMock(return_value=mock_session)
    return repo

@pytest.mark.asyncio
async def test_delete_product_success(repository, mock_session):
    # ARRANGE
    product_id = 1
    # Use a single object to avoid identity mismatches in assertions
    product_to_delete = ProductDAO(
        id=product_id,
        barcode="1234567890128",
        price_per_unit=1.99,
        quantity=10,
        position="A1",
        description="Test Product",
        note="Test Note",
        involvedOperations=0
    )

    mock_session.get.return_value = product_to_delete

    # ACT
    await repository.delete_product(product_id)

    # ASSERT
    mock_session.get.assert_called_once_with(ProductDAO, product_id)
    # Corrected: asserting against the actual object returned by get
    mock_session.delete.assert_called_once_with(product_to_delete)
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_delete_product_not_found(repository, mock_session):
    # ARRANGE
    product_id = 999
    mock_session.get.return_value = None

    # ACT & ASSERT
    with pytest.raises(NotFoundError) as exc_info:
        await repository.delete_product(product_id)
    
    assert "Product not found" in str(exc_info.value)
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()

@pytest.mark.asyncio
async def test_delete_product_invalid_state(repository, mock_session):
    # ARRANGE
    product_id = 1
    # You can use a MagicMock for the DAO object itself as long as it has the attributes
    mock_product = MagicMock(spec=ProductDAO)
    mock_product.involvedOperations = 5 

    mock_session.get.return_value = mock_product

    # ACT & ASSERT
    with pytest.raises(InvalidStateError) as exc_info:
        await repository.delete_product(product_id)
    
    assert "Invalid sale state" in str(exc_info.value)
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()