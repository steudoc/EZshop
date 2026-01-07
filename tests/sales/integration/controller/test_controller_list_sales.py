import pytest
from unittest.mock import MagicMock
from datetime import datetime
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SaleDTO

def create_mock_dao(id_val, status):
    #Helper function to create a "Valid" DAO Mock
    dao = MagicMock()
    dao.id = id_val
    dao.status = status
    dao.created_at = datetime.now()
    dao.closed_at = None
    dao.discount_rate = 0.0
    dao.lines = [] # Empty list required by mapper loop
    return dao

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. Filtering Logic -> "if sale_dao is not None" checks robustness.
# ==============================================================================

@pytest.mark.asyncio
async def test_list_sales_empty(sale_controller, mock_sale_repo):
    """
    Scenario: The repository returns an empty list.
    Expected: An empty list of DTOs.
    """
    # Arrange
    mock_sale_repo.list_sales.return_value = []

    # Act
    result = await sale_controller.list_sales()

    # Assert
    assert isinstance(result, list)
    assert len(result) == 0
    mock_sale_repo.list_sales.assert_called_once()

@pytest.mark.asyncio
async def test_list_sales_success(sale_controller, mock_sale_repo):
    """
    Scenario: The repository returns a list of valid Sales DAOs.
    Expected: A list of SaleDTO objects with correct data.
    """
    # Arrange
    dao1 = create_mock_dao(1, SaleStatus.OPEN)
    dao2 = create_mock_dao(2, SaleStatus.PAID)
    
    mock_sale_repo.list_sales.return_value = [dao1, dao2]

    # Act
    result = await sale_controller.list_sales()

    # Assert
    assert len(result) == 2
    
    # Verify mapping
    assert isinstance(result[0], SaleDTO)
    assert result[0].id == 1
    assert result[0].status == SaleStatus.OPEN
    
    assert isinstance(result[1], SaleDTO)
    assert result[1].id == 2
    assert result[1].status == SaleStatus.PAID

@pytest.mark.asyncio
async def test_list_sales_filtering_logic(sale_controller, mock_sale_repo):
    """
    Scenario: The repository returns a list containing a None value (Dirty Data).
    Logic to test: if sale_dao is not None
    Expected: The None value should be filtered out, returning only the valid DTO.
    """
    # Arrange
    valid_dao = create_mock_dao(1, SaleStatus.OPEN)
    # The list contains one valid object and one None
    dirty_list = [valid_dao, None]
    
    mock_sale_repo.list_sales.return_value = dirty_list

    # Act
    result = await sale_controller.list_sales()

    # Assert
    # Should contain only 1 element (the valid one)
    assert len(result) == 1
    assert result[0].id == 1