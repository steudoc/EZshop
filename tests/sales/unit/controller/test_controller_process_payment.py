import pytest
from unittest.mock import MagicMock, AsyncMock
from app.controllers.sale_controller import SaleController
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SalePaymentDTO
from app.models.DTO.system_dto import SystemInfoDTO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. _get_sale_or_throw -> Checks if Sale exists.
# 2. _validate_sale_status -> Checks if status is PENDING.
# ==============================================================================

@pytest.mark.asyncio
async def test_process_payment_decision_sale_not_found(sale_controller, mock_sale_repo, mock_system_controller):
    """
    DECISION 1: if not sale -> TRUE (Covering _get_sale_or_throw)
    Scenario: The sale ID provided does not exist.
    """
    # Arrange
    payment_dto = SalePaymentDTO(sale_id=999, amount_paid=100.0)
    
    mock_system_controller.get_balance.return_value = SystemInfoDTO(balance=0.0)
    
    # Simulate DB returning None
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.process_payment(payment_dto)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_process_payment_decision_invalid_state_open(sale_controller, mock_sale_repo, mock_system_controller):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != PENDING -> TRUE (Covering _validate_sale_status)
    Scenario: The sale exists but is still OPEN (not closed yet). Payment cannot proceed.
    """
    # Arrange
    payment_dto = SalePaymentDTO(sale_id=1, amount_paid=100.0)
    
    mock_system_controller.get_balance.return_value = SystemInfoDTO(balance=0.0)
    
    # Simulate Sale with WRONG status
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN 
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(InvalidStateError) as excinfo:
        await sale_controller.process_payment(payment_dto)

    assert "sale is not in PENDING state".lower() in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_process_payment_success_calculation(sale_controller, mock_sale_repo, mock_system_controller):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != PENDING -> FALSE
    Scenario: Verify complex math calculation and side effects.
    
    Test Data:
    1. Line 1: Qty 2, Price 50.0, Disc 0.0 -> Cost: 100.0
    2. Line 2: Qty 1, Price 100.0, Disc 0.1 (10%) -> Cost: 90.0
    3. Subtotal: 190.0
    4. Global Sale Discount: 0.1 (10%) -> 190 - 19 = 171.0 (Final Price)
    5. Amount Paid: 200.0
    6. Expected Change: 200.0 - 171.0 = 29.0
    7. Initial Balance: 1000.0 -> New Balance: 1171.0
    """
    # Arrange
    sale_id = 1
    payment_dto = SalePaymentDTO(sale_id=sale_id, amount_paid=200.0)
    
    # 1. Setup System Balance
    mock_system_controller.get_balance.return_value = SystemInfoDTO(balance=1000.0)

    # 2. Setup Lines
    line1 = MagicMock()
    line1.quantity = 2
    line1.price_per_unit = 50.0
    line1.discount_rate = 0.0
    
    line2 = MagicMock()
    line2.quantity = 1
    line2.price_per_unit = 100.0
    line2.discount_rate = 0.1 # 10%

    # 3. Setup Sale
    mock_sale = MagicMock()
    mock_sale.id = sale_id
    mock_sale.status = SaleStatus.PENDING
    mock_sale.discount_rate = 0.1 # 10% global discount
    mock_sale.lines = [line1, line2]
    
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act
    result = await sale_controller.process_payment(payment_dto)

    # Assert
    # A. Check Logic: Change Calculation
    # Expected: 29.0
    assert result.change == 29.0
    
    # B. Check Side Effect: Status Update
    mock_sale_repo.update_sale_status_paid.assert_called_once_with(sale_id)
    
    # C. Check Side Effect: System Balance Update
    # Expected: 1000.0 + 171.0 = 1171.0
    mock_system_controller.set_balance.assert_called_once_with(1171.0)