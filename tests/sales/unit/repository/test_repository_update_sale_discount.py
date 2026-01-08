import pytest
from unittest.mock import MagicMock
from app.models.errors.notfound_error import NotFoundError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# Decisions to cover:
# 1. if not sale (Sale Not Found)
# ==============================================================================

@pytest.mark.asyncio
async def test_update_discount_decision_sale_not_found(sale_repo):
    """
    DECISION 1: if not sale -> TRUE
    Scenario: The sale ID does not exist in the database.
    Expected: Raises NotFoundError.
    """
    # Simulate DB returning None
    sale_repo._get_sale_with_lines.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.update_sale_discount(1, 0.5)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_discount_success(sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    """
    # 1. Create the target line (Current discount = 0.0)
    mock_line = MagicMock()
    mock_line.product_barcode = "123"
    
    # 2. Create the sale
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    mock_sale.discount_rate = 0.0
    
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Act: Update discount to 0.20 (20%)
    new_discount = 0.20
    result = await sale_repo.update_sale_discount(1, new_discount)

    # Assert
    assert result is True
    
    assert mock_sale.discount_rate == new_discount