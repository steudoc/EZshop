import pytest
from unittest.mock import MagicMock
from app.models.errors.notfound_error import NotFoundError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# Decisions to cover:
# 1. if not sale (Sale Not Found)
# 2. if not line_to_update (Sale Line Not Found)
# ==============================================================================

@pytest.mark.asyncio
async def test_update_line_discount_decision_sale_not_found(sale_repo):
    """
    DECISION 1: if not sale -> TRUE
    Scenario: The sale ID does not exist in the database.
    Expected: Raises NotFoundError.
    """
    # Simulate DB returning None
    sale_repo._get_sale_with_lines.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.update_sale_line_discount(1, "123", 0.5)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_line_discount_decision_line_not_found(sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not line_to_update -> TRUE
    Scenario: Sale exists, but it does not contain the requested product barcode.
    Expected: Raises NotFoundError.
    """
    # Create a line with a different barcode
    mock_line = MagicMock()
    mock_line.product_barcode = "OTHER_PRODUCT"
    
    # Create sale containing that line
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Act & Assert
    # We ask to update "TARGET_PRODUCT", which is not in the list
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.update_sale_line_discount(1, "TARGET_PRODUCT", 0.5)

    assert "sale line not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_line_discount_success(sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not line_to_update -> FALSE
    Scenario: Sale exists and contains the specific line.
    Expected: The discount_rate of the line object is updated to the new value.
    """
    # 1. Create the target line (Current discount = 0.0)
    mock_line = MagicMock()
    mock_line.product_barcode = "123"
    mock_line.discount_rate = 0.0
    
    # 2. Create the sale
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Act: Update discount to 0.20 (20%)
    new_discount = 0.20
    result = await sale_repo.update_sale_line_discount(1, "123", new_discount)

    # Assert
    assert result is True
    
    assert mock_line.discount_rate == new_discount