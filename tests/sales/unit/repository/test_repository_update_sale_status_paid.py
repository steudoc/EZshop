import pytest
from unittest.mock import MagicMock
from app.models.errors.notfound_error import NotFoundError
from app.models.sale_status import SaleStatus

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# Decisions to cover:
# 1. if not sale (Sale Not Found)
# ==============================================================================

@pytest.mark.asyncio
async def test_update_status_paid_decision_sale_not_found(sale_repo):
    """
    DECISION 1: if not sale -> TRUE
    Scenario: The sale ID does not exist in the database.
    Expected: Raises NotFoundError.
    """
    # Simulate DB returning None
    sale_repo._get_sale_with_lines.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.update_sale_status_paid(1)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_status_paid_success(sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    """
    # 1. Create the sale
    mock_sale = MagicMock()
    mock_sale.status = SaleStatus.PENDING
    
    sale_repo._get_sale_with_lines.return_value = mock_sale

    result = await sale_repo.update_sale_status_paid(1)

    # Assert
    assert result is True
    
    assert mock_sale.status == SaleStatus.PAID