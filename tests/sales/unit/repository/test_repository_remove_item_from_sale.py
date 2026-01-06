import pytest
from unittest.mock import MagicMock
from app.models.errors.notfound_error import NotFoundError 

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# Decisions to cover:
# 1. if not sale (Sale Not Found)
# 2. if not line_to_remove (Sale Line Not Found)
# 3. if line_to_remove.quantity < quantity (Cap quantity)
# 4. if not product (Product Not Found)
# 5. if line_to_remove.quantity <= 0 (Remove line vs Keep line)
# ==============================================================================

@pytest.mark.asyncio
async def test_remove_item_decision_sale_not_found(sale_repo):
    """
    DECISION 1: if not sale -> TRUE
    """
    sale_repo._get_sale_with_lines.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.remove_item_from_sale(1, "123", 1)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_remove_item_decision_line_not_found(sale_repo):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not line_to_remove -> TRUE
    Scenario: Sale exists, but the product barcode is not in the list.
    """
    mock_sale = MagicMock()
    mock_sale.lines = [] # Empty lines
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.remove_item_from_sale(1, "123", 1)

    assert "sale line not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_remove_item_decision_cap_quantity_and_remove(sale_repo, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not line_to_remove -> FALSE
    DECISION 3: if line.quantity < quantity -> TRUE
    DECISION 4: if not product -> FALSE
    DECISION 5: if line.quantity <= 0 -> TRUE
    Scenario: User wants to remove 10, but line has only 5.
    Expected: Remove 5 (cap), and remove the line completely.
    """
    # Line setup: 5 items
    mock_line = MagicMock()
    mock_line.product_barcode = "123"
    mock_line.quantity = 5
    
    # Sale setup
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Product setup (Stock = 100, Ops = 5)
    mock_product = MagicMock()
    mock_product.quantity = 100
    mock_product.involvedOperations = 5
    mock_product_repo_class.get_product_by_barcode.return_value = mock_product

    # Act: Request to remove 10 (Greater than 5)
    result = await sale_repo.remove_item_from_sale(1, "123", 10)

    # Assert
    assert result is True
    # 1. Check Capping logic: 
    # Stock should increase by 5 (the available amount), not 10
    assert mock_product.quantity == 105 
    
    # 2. Check Line Removal logic:
    # Line quantity became <= 0, so it should be removed from the list
    assert mock_line not in mock_sale.lines
    assert len(mock_sale.lines) == 0
    
    # 3. Check Operation decrement
    assert mock_product.involvedOperations == 4
    
    mock_product_repo_class.update_product.assert_called_once_with(mock_product)

@pytest.mark.asyncio
async def test_remove_item_decision_product_not_found(sale_repo, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not line_to_remove -> FALSE
    DECISION 3: if line.quantity < quantity -> FALSE
    DECISION 4: if not product -> TRUE
    Scenario: Line found, but Product lookup fails (Data inconsistency).
    """
    mock_line = MagicMock()
    mock_line.product_barcode = "123"
    mock_line.quantity = 5

    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Force product not found
    mock_product_repo_class.get_product_by_barcode.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.remove_item_from_sale(1, "123", 1)
        
    assert "product not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_remove_item_decision_partial_removal(sale_repo, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not line_to_remove -> FALSE
    DECISION 3: if line.quantity < quantity -> FALSE
    DECISION 4: if not product -> FALSE
    DECISION 5: if line.quantity <= 0 -> FALSE
    Scenario: Line has 10 items, remove 2.
    Expected: Line remains with 8 items. Operations NOT decremented.
    """
    mock_line = MagicMock()
    mock_line.product_barcode = "123"
    mock_line.quantity = 10

    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Product setup
    mock_product = MagicMock()
    mock_product.quantity = 100
    mock_product.involvedOperations = 5
    mock_product_repo_class.get_product_by_barcode.return_value = mock_product

    # Act: Remove 2
    result = await sale_repo.remove_item_from_sale(1, "123", 2)

    # Assert
    assert result is True
    
    # 1. Check Quantity logic
    # Line quantity: 10 - 2 = 8 (Still > 0)
    assert mock_line.quantity == 8
    # Product Stock: 100 + 2 = 102
    assert mock_product.quantity == 102
    
    # 2. Check Line is NOT removed
    assert mock_line in mock_sale.lines
    assert len(mock_sale.lines) == 1
    
    # 3. Check Operations NOT decremented (Product still in sale)
    assert mock_product.involvedOperations == 5
    
    mock_product_repo_class.update_product.assert_called_once_with(mock_product)