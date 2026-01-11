import pytest
from unittest.mock import MagicMock
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SaleLineDTO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. _get_sale_or_throw -> Checks if Sale exists.
# 2. _validate_sale_status -> Checks if status is OPEN.
# ==============================================================================

@pytest.mark.asyncio
async def test_add_item_decision_sale_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> TRUE (Covering _get_sale_or_throw)
    Scenario: The sale ID provided in the DTO does not exist in the database.
    """
    # Arrange
    dto = SaleLineDTO(sale_id=999, product_barcode="123456789012", quantity=1)
    
    # Simulate DB returning None
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.add_item_to_sale(dto)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_add_item_decision_invalid_state(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> TRUE (Covering _validate_sale_status)
    Scenario: The sale exists but is already PAID. Items cannot be added.
    """
    # Arrange
    dto = SaleLineDTO(sale_id=1, product_barcode="123456789012", quantity=1)
    
    # Simulate an existing sale with WRONG status
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.PAID 
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(InvalidStateError) as excinfo:
        await sale_controller.add_item_to_sale(dto)

    assert "sale is not in OPEN state".lower() in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_add_item_success(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    Scenario: Sale exists, is OPEN, and Repo is called correctly.
    """
    # Arrange
    sale_id = 1
    barcode = "123456789012"
    qty = 5
    dto = SaleLineDTO(sale_id=sale_id, product_barcode=barcode, quantity=qty)
    
    # Simulate a valid OPEN sale
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act
    # The method returns None, so we just await it
    await sale_controller.add_item_to_sale(dto)

    # Assert
    # Verify that the repository method was called with the unpacked values from the DTO
    mock_sale_repo.add_item_to_sale.assert_called_once_with(sale_id, barcode, qty)