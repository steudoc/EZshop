import pytest
from unittest.mock import MagicMock
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SaleDiscountDTO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.bad_request import BadRequestError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. _get_sale_or_throw -> Checks if Sale exists.
# 2. _validate_sale_status -> Checks if status is OPEN.
# 3. if not result -> If repo returns False, throw BadRequest.
# ==============================================================================

@pytest.mark.asyncio
async def test_update_discount_decision_sale_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> TRUE (Covering _get_sale_or_throw)
    Scenario: The sale ID provided does not exist in the database.
    """
    # Arrange
    dto = SaleDiscountDTO(id=999, discount_rate=0.5)
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.update_sale_discount(dto)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_discount_decision_invalid_state(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> TRUE (Covering _validate_sale_status)
    Scenario: The sale exists but is already PAID or PENDING. Discount cannot be changed.
    """
    # Arrange
    dto = SaleDiscountDTO(id=1, discount_rate=0.5)
    
    # Simulate an existing sale with WRONG status
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.PAID 
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(InvalidStateError) as excinfo:
        await sale_controller.update_sale_discount(dto)

    assert "sale is not in OPEN state".lower() in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_discount_decision_repo_fail(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    DECISION 3: if not result -> TRUE
    Scenario: Sale exists and is OPEN, but the repository operation fails (returns False).
    """
    # Arrange
    dto = SaleDiscountDTO(id=1, discount_rate=0.5)
    
    # Simulate valid sale
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Force Repository Failure
    mock_sale_repo.update_sale_discount.return_value = False

    # Act & Assert
    with pytest.raises(BadRequestError) as excinfo:
        await sale_controller.update_sale_discount(dto)
    
    assert "failed to update" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_discount_success(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    DECISION 3: if not result -> FALSE
    Scenario: Sale exists, is OPEN, and Repo updates successfully.
    """
    # Arrange
    sale_id = 1
    discount = 0.25
    dto = SaleDiscountDTO(id=sale_id, discount_rate=discount)
    
    # Simulate valid sale
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Force Repository Success
    mock_sale_repo.update_sale_discount.return_value = True

    # Act
    result = await sale_controller.update_sale_discount(dto)

    # Assert
    # 1. Verify return value
    assert result.success is True 
    
    # 2. Verify delegation to repository with correct arguments
    mock_sale_repo.update_sale_discount.assert_called_once_with(sale_id, discount)