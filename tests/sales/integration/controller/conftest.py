import pytest
from unittest.mock import AsyncMock
from app.controllers.sale_controller import SaleController

# ==============================================================================
# FIXTURES (SETUP)
# ==============================================================================

@pytest.fixture
def mock_sale_repo():
    """Mocks the SaleRepository to avoid DB connection."""
    return AsyncMock()

@pytest.fixture
def mock_system_controller():
    """Mocks the SystemController."""
    return AsyncMock()

@pytest.fixture
def sale_controller(mock_sale_repo, mock_system_controller):
    """
    Creates the Controller instance and manually injects the mocks.
    This ensures complete isolation from the backend.
    """
    #Force reset the Singleton instance before testing
    SaleController._instance = None

    controller = SaleController()
    controller.sale_repo = mock_sale_repo
    controller.system_controller = mock_system_controller
    return controller