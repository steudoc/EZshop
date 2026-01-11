import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.repositories.sale_repository import SaleRepository

# ==============================================================================
# SETUP & FIXTURES
# ==============================================================================

@pytest.fixture
def mock_session():
    """Mocks the database session (Async Context Manager)."""
    session = AsyncMock()
    # Setup needed for 'async with await self._get_session() as session:'
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None

    session.add = MagicMock()
    
    return session

@pytest.fixture
def sale_repo(mock_session):
    """Creates the SaleRepository with a mocked _get_session method."""
    repo = SaleRepository()
    # Mock the internal helper _get_session
    repo._get_session = AsyncMock(return_value=mock_session)
    # Mock the internal helper _get_sale_with_lines
    repo._get_sale_with_lines = AsyncMock() 
    return repo

@pytest.fixture
def mock_product_repo_class():
    with patch("app.repositories.sale_repository.ProductRepository") as MockClass:
        # The MockClass returns an instance (the mock_repo)
        mock_instance = MockClass.return_value
        # Setup async methods on the instance
        mock_instance.get_product_by_barcode = AsyncMock()
        mock_instance.update_product = AsyncMock()
        yield mock_instance