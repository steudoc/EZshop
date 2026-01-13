import pytest
from unittest.mock import MagicMock
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SaleLineDTO
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.bad_request import BadRequestError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. _get_sale_or_throw -> Checks if Sale exists.
# 2. _validate_sale_status -> Checks if status is OPEN.
# 3. Line Existence Check -> Checks if product is in the sale.
# 4. Quantity Check -> Checks if enough quantity exists to remove.
# ==============================================================================

@pytest.mark.asyncio
async def test_delete_item_decision_sale_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> TRUE
    Scenario: The sale ID provided does not exist.
    """
    # Arrange
    dto = SaleLineDTO(sale_id=999, product_barcode="123", quantity=1)
    mock_sale_repo.get_sale_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.delete_item_from_sale(dto)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_delete_item_decision_invalid_state(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> TRUE
    Scenario: The sale exists but is PAID.
    """
    # Arrange
    dto = SaleLineDTO(sale_id=1, product_barcode="123", quantity=1)
    
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.PAID 
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(InvalidStateError) as excinfo:
        await sale_controller.delete_item_from_sale(dto)

    assert "sale is not in OPEN state".lower() in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_delete_item_decision_line_not_found(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    DECISION 3: if not sale_lines -> TRUE
    Scenario: Sale exists and is OPEN, but the product barcode is NOT in the list.
    Expected: NotFoundError.
    """
    # Arrange
    dto = SaleLineDTO(sale_id=1, product_barcode="GHOST_ITEM", quantity=1)
    
    # Create a sale with NO lines
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale.lines = [] # Empty list
    
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_controller.delete_item_from_sale(dto)
    
    assert "product in sale line  not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_delete_item_decision_insufficient_quantity(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    DECISION 3: if not sale_lines -> FALSE
    DECISION 4: if sale_lines.quantity < item_dto.quantity -> TRUE
    Scenario: User tries to remove 5 items, but the line only has 2.
    Expected: BadRequestError.
    """
    # Arrange
    barcode = "ITEM_123"
    current_qty = 2
    remove_qty = 5
    dto = SaleLineDTO(sale_id=1, product_barcode=barcode, quantity=remove_qty)
    
    # Create the line inside the sale
    mock_line = MagicMock()
    mock_line.product_barcode = barcode
    mock_line.quantity = current_qty

    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale.lines = [mock_line]
    
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act & Assert
    with pytest.raises(BadRequestError) as excinfo:
        await sale_controller.delete_item_from_sale(dto)

    assert "not enough quantity" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_delete_item_success(sale_controller, mock_sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if status != OPEN -> FALSE
    DECISION 3: if not sale_lines -> FALSE
    DECISION 4: if sale_lines.quantity < item_dto.quantity -> FALSE
    Scenario: Everything is correct.
    """
    # Arrange
    barcode = "123456789"
    current_qty = 10
    remove_qty = 2
    
    dto = SaleLineDTO(sale_id=1, product_barcode=barcode, quantity=remove_qty)
    
    # Create VALID line
    mock_line = MagicMock()
    mock_line.product_barcode = barcode
    mock_line.quantity = current_qty

    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.OPEN
    mock_sale.lines = [mock_line]
    
    mock_sale_repo.get_sale_by_id.return_value = mock_sale

    # Act
    result = await sale_controller.delete_item_from_sale(dto)

    # Assert
    assert result.success is True
    # Check that repo is called
    mock_sale_repo.remove_item_from_sale.assert_called_once_with(1, barcode, remove_qty)