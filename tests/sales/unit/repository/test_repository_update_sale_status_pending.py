import pytest
from unittest.mock import MagicMock
from app.models.errors.notfound_error import NotFoundError
from app.models.sale_status import SaleStatus
from datetime import datetime

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# Decisions to cover:
# 1. if not sale (Sale Not Found)
# 2. if not sale.lines (Sale Line Not Found)
# ==============================================================================

@pytest.mark.asyncio
async def test_update_status_pending_decision_sale_not_found(sale_repo):
    """
    DECISION 1: if not sale -> TRUE
    """
    # Simulate DB returning None
    sale_repo._get_sale_with_lines.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.update_sale_status_pending(1)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_update_status_pending_decision_line_found(sale_repo, mock_session):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not sale.lines -> FALSE
    """ 
    mock_line = MagicMock()
    
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    mock_sale.status = SaleStatus.OPEN
    mock_sale.closed_at = None
    
    sale_repo._get_sale_with_lines.return_value = mock_sale

    result = await sale_repo.update_sale_status_pending(1)

    # Assert
    assert result is True
    assert mock_sale.status == SaleStatus.PENDING

    mock_session.delete.assert_not_called()

@pytest.mark.asyncio
async def test_update_status_pending_decision_line_not_found(sale_repo, mock_session):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not sale.lines -> TRUE
    """    
    # Create the sale
    mock_sale = MagicMock()
    mock_sale.lines = []
    mock_sale.status = SaleStatus.OPEN
    mock_sale.closed_at = None
    
    sale_repo._get_sale_with_lines.return_value = mock_sale

    result = await sale_repo.update_sale_status_pending(1)

    # Assert
    assert result is True

    mock_session.delete.assert_called_once()