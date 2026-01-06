import pytest
from unittest.mock import MagicMock
from app.models.sale_status import SaleStatus
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. _get_sale_or_throw -> Checks if Sale exists.
# 2. if sale_dao.status == SaleStatus.PAID -> Checks if status is allowed (NOT PAID).
# ==============================================================================

@pytest.mark.asyncio
async def test_delete_sale_decision_sale_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> TRUE (Covering _get_sale_or_throw)
    Scenario: The sale ID provided does not exist in the database.
    """
    # Arrange
    sale_id = 999
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.delete_sale(sale_id)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_delete_sale_decision_invalid_state_paid(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if sale_dao.status == PAID -> TRUE
    Scenario: The sale exists but is already PAID. A finalized sale usually cannot be deleted.
    """
    # Arrange
    sale_id = 1
    
    # Simulate an existing sale with PAID status
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.PAID 
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(InvalidStateError) as excinfo:
        await sale_controller.delete_sale(sale_id)

    assert "Cannot delete this sale".lower() in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_delete_sale_success(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if sale_dao.status == PAID -> FALSE
    Scenario: Sale exists, is OPEN, and is deleted successfully.
    """
    # Arrange
    sale_id = 1
    
    # Simulate a valid OPEN sale
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Mock the return value of the repo delete function (if it returns boolean)
    mock_sale_repo.delete_sale.return_value = True

    # Act
    await sale_controller.delete_sale(sale_id)

    # Assert    
    # Verify delegation: The controller must call the repository delete method
    mock_sale_repo.delete_sale.assert_called_once_with(sale_id)