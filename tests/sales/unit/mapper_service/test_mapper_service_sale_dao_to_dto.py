from datetime import datetime
from unittest.mock import MagicMock
from app.models.sale_status import SaleStatus
from app.models.DTO.sale_dto import SaleDTO, SaleLineDTO
from app.services.mapper_service import sale_dao_to_dto

# ==============================================================================
# TEST SUITE: Simple Decision Coverage
#
# Logic to cover:
# 1. Input None -> Output None
# 2. Input Empty Sale -> Output Empty DTO
# 3. Input Sale with Lines -> Output DTO with mapped lines
# ==============================================================================

def test_sale_mapper_none_input():
    """
    Scenario: Input is None.
    Expected: Output should be None (safety check).
    """
    # Act
    result = sale_dao_to_dto(None)

    # Assert
    assert result is None

def test_sale_mapper_empty_sale():
    """
    Scenario: Input is a valid SaleDAO but with NO lines.
    Expected: Output is a SaleDTO with empty 'lines' list.
    """
    # Arrange: Create a fake DAO object
    mock_dao = MagicMock()
    mock_dao.id = 1
    mock_dao.status = SaleStatus.OPEN
    mock_dao.created_at = datetime.now()
    mock_dao.closed_at = None
    mock_dao.discount_rate = 0.0
    mock_dao.lines = [] # Empty lines

    # Act
    result = sale_dao_to_dto(mock_dao)

    # Assert
    assert isinstance(result, SaleDTO)
    assert result.id == 1
    assert result.status == SaleStatus.OPEN
    assert result.lines == []
    assert result.discount_rate == 0.0

def test_sale_mapper_with_lines():
    """
    Scenario: Input is a SaleDAO with 2 lines.
    Expected: Output is a SaleDTO containing a list of 2 SaleLineDTOs.
    """
    # Arrange: Create fake Line DAOs
    line1 = MagicMock()
    line1.id = 101
    line1.sale_id = 1
    line1.product_barcode = "ABC"
    line1.quantity = 2
    line1.price_per_unit = 10.0
    line1.discount_rate = 0.0

    line2 = MagicMock()
    line2.id = 102
    line2.sale_id = 1
    line2.product_barcode = "XYZ"
    line2.quantity = 1
    line2.price_per_unit = 20.0
    line2.discount_rate = 0.5

    # Arrange: Create fake Sale DAO
    mock_dao = MagicMock()
    mock_dao.id = 1
    mock_dao.status = SaleStatus.PENDING
    mock_dao.created_at = datetime.now()
    mock_dao.closed_at = None
    mock_dao.discount_rate = 0.1
    mock_dao.lines = [line1, line2]

    # Act
    result = sale_dao_to_dto(mock_dao)

    # Assert
    # 1. Check Sale properties
    assert result.id == 1
    assert result.status == SaleStatus.PENDING
    assert result.discount_rate == 0.1
    assert len(result.lines) == 2

    # 2. Check Line 1 properties
    dto_line1 = result.lines[0]
    assert isinstance(dto_line1, SaleLineDTO)
    assert dto_line1.id == 101
    assert dto_line1.product_barcode == "ABC"
    assert dto_line1.quantity == 2
    assert dto_line1.price_per_unit == 10.0
    
    # 3. Check Line 2 properties
    dto_line2 = result.lines[1]
    assert isinstance(dto_line2, SaleLineDTO)
    assert dto_line2.product_barcode == "XYZ"
    assert dto_line2.discount_rate == 0.5