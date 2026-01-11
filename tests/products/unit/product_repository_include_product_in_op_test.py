from app.repositories.product_repository import ProductRepository
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.bad_request import BadRequestError
from app.models.DAO.product_dao import ProductDAO


@pytest.fixture
def mock_session():
    """
    Creates a mock database session with all necessary async methods.
    """
    session = MagicMock()
    # Async Context Manager
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    # Async Methods - all awaited methods must be AsyncMock
    session.get = AsyncMock()
    session.flush = AsyncMock() # Added this to fix the TypeError
    return session

@pytest.fixture
def repository(mock_session):
    """Initializes the repository with the injected mock session."""
    repo = ProductRepository()
    repo._get_session = AsyncMock(return_value=mock_session)
    return repo

# --- Tests ---

@pytest.mark.asyncio
async def test_include_product_in_op_increment_success(repository, mock_session):
    # ARRANGE
    product_id = 1
    mock_product = MagicMock(spec=ProductDAO)
    mock_product.involvedOperations = 5
    mock_session.get.return_value = mock_product

    # ACT
    await repository.include_product_in_op(product_id, include=True)

    # ASSERT
    assert mock_product.involvedOperations == 6
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_include_product_in_op_decrement_success(repository, mock_session):
    # ARRANGE
    product_id = 1
    mock_product = MagicMock(spec=ProductDAO)
    mock_product.involvedOperations = 1
    mock_session.get.return_value = mock_product

    # ACT
    await repository.include_product_in_op(product_id, include=False)

    # ASSERT
    assert mock_product.involvedOperations == 0
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_include_product_in_op_decrement_below_zero(repository, mock_session):
    # ARRANGE
    product_id = 1
    mock_product = MagicMock(spec=ProductDAO)
    mock_product.involvedOperations = 0
    mock_session.get.return_value = mock_product

    # ACT & ASSERT
    with pytest.raises(BadRequestError) as exc_info:
        await repository.include_product_in_op(product_id, include=False)
    
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio 
async def test_include_product_in_op_not_found(repository, mock_session):
    # ARRANGE
    product_id = 999
    mock_session.get.return_value = None

    # ACT & ASSERT
    with pytest.raises(NotFoundError) as exc_info:
        await repository.include_product_in_op(product_id, include=True)
    
    mock_session.flush.assert_not_called()