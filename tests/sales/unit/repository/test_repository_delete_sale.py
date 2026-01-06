import pytest
from unittest.mock import MagicMock
from app.models.errors.notfound_error import NotFoundError

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
# ==============================================================================

@pytest.mark.asyncio
async def test_delete_sale_decision_not_found(sale_repo, mock_session):
    """
    DECISION 1: if not sale -> TRUE
    """
    sale_id = 1
    # Mock return value to simulate sale not found
    sale_repo._get_sale_with_lines.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as excinfo:
        await sale_repo.delete_sale(sale_id)
    
    assert "sale not found" in str(excinfo.value).lower()
    
    # Verify that it did NOT try to delete anything
    mock_session.delete.assert_not_called()

@pytest.mark.asyncio
async def test_delete_sale_loop_zero_items(sale_repo, mock_session, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    LOOP: 0 Iterations (Empty list)
    Scenario: Empty sale, must be deleted without touching products.
    """
    mock_sale = MagicMock()
    mock_sale.lines = [] # Empty list
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # Act
    await sale_repo.delete_sale(1)

    # Assert
    # 1. Should not have looked up products
    mock_product_repo_class.get_product_by_barcode.assert_not_called()
    # 2. Should have called session.delete(sale)
    mock_session.delete.assert_called_once_with(mock_sale)

@pytest.mark.asyncio
async def test_delete_sale_decision_product_found(sale_repo, mock_session, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    LOOP: 1 Iteration
    DECISION 2: if product -> TRUE
    Scenario: Sale with 1 line. The product exists.
    Verification: Quantity restored and involvedOperations decremented.
    """
    # 1. Create the sale line (Quantity = 5)
    mock_line = MagicMock()
    mock_line.product_barcode = "123"
    mock_line.quantity = 5

    # 2. Create the sale
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # 3. Create the product in DB (Current Quantity = 10, Ops = 5)
    mock_product = MagicMock()
    mock_product.quantity = 10
    mock_product.involvedOperations = 5
    mock_product_repo_class.get_product_by_barcode.return_value = mock_product

    # Act
    await sale_repo.delete_sale(1)

    # Assert
    # A. Verify mathematical calculations on the mock
    # 10 (stock) + 5 (returned) = 15
    assert mock_product.quantity == 15 
    # 5 (ops) - 1 = 4
    assert mock_product.involvedOperations == 4

    # B. Verify calls
    mock_product_repo_class.update_product.assert_called_once_with(mock_product)
    mock_session.delete.assert_called_once_with(mock_sale)

@pytest.mark.asyncio
async def test_delete_sale_decision_product_not_found(sale_repo, mock_session, mock_product_repo_class):
    """
    DECISION 1: if not sale -> FALSE
    LOOP: 1 Iteration
    DECISION 2: if product -> FALSE
    Scenario: Sale has a line, but the associated product was deleted from DB.
    (get_product_by_barcode returns None).
    Verification: The code must not crash, must skip the update, and delete the sale.
    """
    mock_line = MagicMock()
    mock_line.product_barcode = "GHOST_PRODUCT"
    
    mock_sale = MagicMock()
    mock_sale.lines = [mock_line]
    sale_repo._get_sale_with_lines.return_value = mock_sale

    # The product is not found
    mock_product_repo_class.get_product_by_barcode.return_value = None

    # Act
    await sale_repo.delete_sale(1)

    # Assert
    # update_product MUST NOT be called (otherwise it would crash on None)
    mock_product_repo_class.update_product.assert_not_called()
    
    # The sale must be deleted anyway
    mock_session.delete.assert_called_once_with(mock_sale)