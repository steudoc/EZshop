import pytest
from unittest.mock import MagicMock
from app.models.sale_status import SaleStatus
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.bad_request import BadRequestError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. _get_sale_or_throw -> Checks if Sale exists.
# 2. _validate_sale_status -> Checks if status is OPEN.
# 3. if not result
# ==============================================================================

@pytest.mark.asyncio
async def test_close_sale_decision_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> TRUE (Covering _get_sale_or_throw)
    Scenario: The sale ID provided does not exist in the database.
    """
    # Arrange
    sale_id = 999
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.close_sale(sale_id)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_close_sale_decision_invalid_state(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> TRUE (Covering _validate_sale_status)
    Scenario: The sale exists but is already PAID. It cannot be closed again.
    """
    # Arrange
    sale_id = 1
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.PAID # Invalid state for closing
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(InvalidStateError) as excinfo:
        await sale_controller.close_sale(sale_id)

    assert "sale is not in OPEN state".lower() in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_close_sale_decision_update_failed(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    DECISION 3: if not result -> TRUE
    Scenario: Sale is valid and OPEN, but the Repository fails to update (returns False).
    This covers the `if not result: throw_bad_request` block.
    """
    # Arrange
    sale_id = 1
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Force the repository update to fail
    mock_sale_repo.update_sale_status_pending.return_value = False

    # Act & Assert
    with pytest.raises(BadRequestError) as excinfo:
        await sale_controller.close_sale(sale_id)
    
    # Verify checking for failure message
    assert "failed to close" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_close_sale_success(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    DECISION 3: if not result -> FALSE
    Scenario: Sale exists, is OPEN, and Repo updates successfully.
    """
    # Arrange
    sale_id = 1
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Force the repository update to succeed
    mock_sale_repo.update_sale_status_pending.return_value = True

    # Act
    result = await sale_controller.close_sale(sale_id)

    # Assert
    # 1. Verify return value
    assert result.success is True
    
    # 2. Verify the repository was called exactly once with the correct ID
    mock_sale_repo.update_sale_status_pending.assert_called_once_with(sale_id)