import pytest
from unittest.mock import MagicMock
from datetime import datetime
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SaleDTO
from app.models.errors.notfound_error import NotFoundError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. _get_sale_or_throw -> Checks if Sale exists (Returns DAO or Throws Error).
# ==============================================================================

@pytest.mark.asyncio
async def test_get_sale_decision_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> TRUE (Covering _get_sale_or_throw)
    Scenario: The sale ID provided does not exist in the database.
    Expected: NotFoundError is raised.
    """
    # Arrange
    sale_id = 999
    # Simulate DB returning None
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.get_sale(sale_id)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_get_sale_success(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    Scenario: The sale exists.
    Expected: The controller returns a valid SaleDTO object.
    """
    # Arrange
    sale_id = 1
    
    mock_sale_dao = MagicMock()
    mock_sale_dao.id = sale_id
    mock_sale_dao.status = SaleStatus.OPEN
    mock_sale_dao.created_at = datetime.now()
    mock_sale_dao.closed_at = None
    mock_sale_dao.discount_rate = 0.0
    mock_sale_dao.lines = [] # Empty list needed for the loop in mapper
    
    # Simulate DB returning the DAO
    mock_sale_repo.get_sale_by_id.return_value = mock_sale_dao

    # Act
    result = await sale_controller.get_sale(sale_id)

    # Assert
    # 1. Check that the Repo was called correctly
    mock_sale_repo.get_sale_by_id.assert_called_once_with(sale_id)
    
    # 2. Check that the result is a DTO
    assert isinstance(result, SaleDTO)
    assert result.id == sale_id
    assert result.status == SaleStatus.OPEN