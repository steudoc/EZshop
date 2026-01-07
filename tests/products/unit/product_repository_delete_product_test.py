import pytest
from unittest.mock import MagicMock
from app.exceptions import NotFoundError, InvalidStateError
from app.models.product_dao import ProductDAO

@pytest.mark.asyncio
async def test_delete_product_success(repository, mock_session):
    """
    Test that a product is successfully deleted when found and 
    involvedOperations is 0.
    """
    # ARRANGE
    product_id = 1
    # Create a mock product object
    mock_product = MagicMock(spec=ProductDAO)
    mock_product.id = product_id
    mock_product.involvedOperations = 0  # Valid state for deletion

    # Configure the session to return this product
    mock_session.get.return_value = mock_product

    # ACT
    await repository.delete_product(product_id)

    # ASSERT
    # Verify the repository searched for the correct ID
    mock_session.get.assert_called_once_with(ProductDAO, product_id)
    # Verify the delete method was called on the specific product object
    mock_session.delete.assert_called_once_with(mock_product)
    # Verify changes were flushed to the database
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_delete_product_not_found(repository, mock_session):
    """
    Test that delete_product raises NotFoundError if the product 
    does not exist in the database.
    """
    # ARRANGE
    product_id = 999
    # Simulate database returning None (product not found)
    mock_session.get.return_value = None

    # ACT & ASSERT
    with pytest.raises(NotFoundError) as exc_info:
        await repository.delete_product(product_id)
    
    assert "Product not found" in str(exc_info.value)
    
    # Critical: Ensure no delete operation was attempted
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()

@pytest.mark.asyncio
async def test_delete_product_invalid_state(repository, mock_session):
    """
    Test that delete_product raises InvalidStateError if the product 
    has involvedOperations > 0.
    """
    # ARRANGE
    product_id = 1
    mock_product = MagicMock(spec=ProductDAO)
    mock_product.id = product_id
    mock_product.involvedOperations = 5  # Invalid state: product is in use

    mock_session.get.return_value = mock_product

    # ACT & ASSERT
    with pytest.raises(InvalidStateError) as exc_info:
        await repository.delete_product(product_id)
    
    assert "Invalid sale state" in str(exc_info.value)

    # Critical: Ensure no delete operation was attempted
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()