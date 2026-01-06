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
# 2. _validate_sale_status -> Checks if status is PAID (Points valid only after payment).
# ==============================================================================

@pytest.mark.asyncio
async def test_get_points_decision_sale_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> TRUE (Covering _get_sale_or_throw)
    Scenario: The sale ID provided does not exist in the database.
    """
    # Arrange
    sale_id = 999
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.get_sale_points(sale_id)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_get_points_decision_invalid_state_open(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != PAID -> TRUE (Covering _validate_sale_status)
    Scenario: The sale exists but is still OPEN. Points cannot be computed yet.
    """
    # Arrange
    sale_id = 1
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN # Invalid state for points
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(InvalidStateError) as excinfo:
        await sale_controller.get_sale_points(sale_id)

    assert "sale is not in PAID state".lower() in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_get_points_success_calculation(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != PAID -> FALSE
    Scenario: Sale is PAID. Verify the points calculation.
    """
    # Arrange
    sale_id = 1
    
    # Setup Lines
    # Line 1: 2 items at 50.0 each = 100.0
    line1 = MagicMock()
    line1.quantity = 2
    line1.price_per_unit = 50.0
    line1.discount_rate = 0.0
    
    # Line 2: 1 item at 20.0 = 20.0
    line2 = MagicMock()
    line2.quantity = 1
    line2.price_per_unit = 20.0
    line2.discount_rate = 0.0

    # Setup Sale (Total Value = 120.0)
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.PAID
    mock_sale.lines = [line1, line2]
    mock_sale.discount_rate = 0.0 # No global discount
    
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act
    result = await sale_controller.get_sale_points(sale_id)

    # Assert
    # Total = 120.0 -> Points should be 12
    assert result.points == 12