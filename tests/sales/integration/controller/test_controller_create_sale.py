import pytest
from unittest.mock import MagicMock
from datetime import datetime
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SaleDTO

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# ==============================================================================

@pytest.mark.asyncio
async def test_create_sale_success(sale_controller, mock_sale_repo):
    """
    Scenario: Repository successfully creates a new sale.
    Expected: Controller returns a new SaleDTO with correct ID and OPEN status.
    """
    # Arrange
    new_id = 100
    
    # Create a valid Mock DAO to simulate DB response
    mock_sale_dao = MagicMock()
    mock_sale_dao.id = new_id
    mock_sale_dao.status = SaleStatus.OPEN
    mock_sale_dao.created_at = datetime.now()
    mock_sale_dao.closed_at = None
    mock_sale_dao.discount_rate = 0.0
    mock_sale_dao.lines = [] # New sale starts empty
    
    # Simulate Repo returning the new DAO
    mock_sale_repo.create_sale.return_value = mock_sale_dao

    # Act
    result = await sale_controller.create_sale()

    # Assert
    mock_sale_repo.create_sale.assert_called_once()
    
    # 2. Verify result is a valid DTO
    assert isinstance(result, SaleDTO)
    assert result.id == new_id
    assert result.status == SaleStatus.OPEN
    assert result.lines == []

@pytest.mark.asyncio
async def test_create_sale_repo_failure(sale_controller, mock_sale_repo):
    """
    Scenario: Repository fails to create sale and returns None
    Expected: Controller returns None (since mapper handles None).
    """
    # Arrange
    mock_sale_repo.create_sale.return_value = None

    # Act
    result = await sale_controller.create_sale()

    # Assert
    # Verify that the controller handles None gracefully without crashing
    assert result is None
    mock_sale_repo.create_sale.assert_called_once()