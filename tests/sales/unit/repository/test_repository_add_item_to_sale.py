import pytest
from unittest.mock import MagicMock
from app.models.errors.bad_request import BadRequestError
from app.models.errors.notfound_error import NotFoundError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# Decisions to cover:
# 1. if not sale (Sale Not Found)
# 2. if not product (Product Not Found)
# 3. if product.quantity < quantity (Insufficient Stock)
# 4. if existing_line (True -> Update, False -> Create New)
# ==============================================================================

@pytest.mark.asyncio
async def test_add_item_decision_sale_not_found(sale_repo):
    """
    DECISION 1: if not sale -> TRUE
    """
    sale_id = 1
    # Mock internal call to return None
    sale_repo._get_sale_with_lines.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.add_item_to_sale(sale_id, "123", 1)
    
    assert "sale not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_add_item_decision_product_not_found(sale_repo, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not product -> TRUE
    """
    sale_id = 1
    # Mock sale exists
    mock_sale = MagicMock()
    sale_repo._get_sale_with_lines.return_value = mock_sale
    
    # Mock product returns None
    mock_product_repo_class.get_product_by_barcode.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.add_item_to_sale(sale_id, "999", 1)

    assert "product with barcode '999' not found" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_add_item_decision_insufficient_stock(sale_repo, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not product -> FALSE
    DECISION 3: if product.quantity < quantity -> TRUE
    """
    # Mock sale
    sale_repo._get_sale_with_lines.return_value = MagicMock()
    
    # Mock product with low stock
    mock_product = MagicMock()
    mock_product.quantity = 5
    mock_product_repo_class.get_product_by_barcode.return_value = mock_product

    # Act & Assert (Request 10, but have 5)
    with pytest.raises(BadRequestError) as excinfo:
        await sale_repo.add_item_to_sale(1, "123", 10)

    assert "not enough quantity" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_add_item_decision_existing_line_false(sale_repo, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not product -> FALSE
    DECISION 3: if product.quantity < quantity -> FALSE
    DECISION 4: if existing_line -> FALSE
    """
    # Mock Sale with NO lines
    mock_sale = MagicMock()
    mock_sale.id = 1
    mock_sale.lines = [] # Empty list -> existing_line will be None
    sale_repo._get_sale_with_lines.return_value = mock_sale
    
    # Mock Product with enough stock
    mock_product = MagicMock()
    mock_product.quantity = 100
    mock_product.price_per_unit = 50.0
    mock_product.involvedOperations = 0
    mock_product_repo_class.get_product_by_barcode.return_value = mock_product

    # Act
    result = await sale_repo.add_item_to_sale(1, "123", 10)

    # Assert
    assert result is True
    # Verify new line added
    assert len(mock_sale.lines) == 1
    assert mock_sale.lines[0].quantity == 10
    assert mock_sale.lines[0].product_barcode == "123"
    # Verify product updated
    assert mock_product.involvedOperations == 1
    assert mock_product.quantity == 90 # 100 - 10
    mock_product_repo_class.update_product.assert_called_once_with(mock_product)

@pytest.mark.asyncio
async def test_add_item_decision_existing_line_true(sale_repo, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    DECISION 2: if not product -> FALSE
    DECISION 3: if product.quantity < quantity -> FALSE
    DECISION 4: if existing_line -> TRUE
    """
    # Mock existing line
    mock_line = MagicMock()
    mock_line.product_barcode = "123"
    mock_line.quantity = 5
    
    # Mock Sale with existing line
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    sale_repo._get_sale_with_lines.return_value = mock_sale
    
    # Mock Product
    mock_product = MagicMock()
    mock_product.quantity = 100
    mock_product.involvedOperations = 5
    mock_product_repo_class.get_product_by_barcode.return_value = mock_product

    # Act
    result = await sale_repo.add_item_to_sale(1, "123", 10)

    # Assert
    assert result is True
    # Verify existing line quantity increased
    assert mock_line.quantity == 15 # 5 + 10
    # Verify NO new line added (still 1 object)
    assert len(mock_sale.lines) == 1
    # Verify product update
    assert mock_product.involvedOperations == 5 
    assert mock_product.quantity == 90
    mock_product_repo_class.update_product.assert_called_once_with(mock_product)