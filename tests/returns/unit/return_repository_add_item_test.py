import pytest
from unittest.mock import ANY, AsyncMock, MagicMock
from sqlalchemy.orm import selectinload
from app.models.DAO.return_dao import ReturnDAO, ReturnLineDAO
from app.models.DTO.return_dto import ReturnItemDTO
from app.models.errors.notfound_error import NotFoundError
from app.repositories.return_repository import ReturnRepository

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_repo(mock_session):
    repo = ReturnRepository()
    repo._get_session = AsyncMock()
    repo._get_session.return_value.__aenter__.return_value = mock_session
    repo._get_session.return_value.__aexit__.return_value = None
    return repo



@pytest.mark.asyncio
async def test_add_item_success(mock_repo, mock_session):

    return_tx = MagicMock(spec=ReturnDAO)
    mock_session.get.return_value = return_tx

    item = ReturnItemDTO(
        product_barcode="ABC123",
        quantity=2,
        price_per_unit=10.0
    )

    result = await mock_repo.add_item(return_id=1, item=item)

    assert result == return_tx

    mock_session.get.assert_awaited_once_with(
        ReturnDAO,
        1,
        options=ANY
    )

    mock_session.add.assert_called_once()
    added_line = mock_session.add.call_args[0][0]

    assert isinstance(added_line, ReturnLineDAO)
    assert added_line.product_barcode == "ABC123"
    assert added_line.quantity == 2
    assert added_line.price_per_unit == 10.0
    assert added_line.return_id == 1

    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(return_tx)


@pytest.mark.asyncio
async def test_add_item_return_not_found(mock_repo, mock_session):

    mock_session.get.return_value = None

    item = ReturnItemDTO(
        product_barcode="ABC123",
        quantity=1,
        price_per_unit=5.0
    )

    with pytest.raises(NotFoundError) as exc_info:
        result = await mock_repo.add_item(return_id=99, item=item)

        assert result is None

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_item_existing_line_increases_quantity(mock_repo, mock_session):

    existing_line = ReturnLineDAO(
        return_id=1,
        product_barcode="ABC123",
        quantity=2,
        price_per_unit=10.0
    )

    return_tx = MagicMock(spec=ReturnDAO)
    return_tx.lines = [existing_line]

    mock_session.get = AsyncMock(return_value=return_tx)

    item = ReturnItemDTO(
        product_barcode="ABC123",
        quantity=3,
        price_per_unit=10.0
    )

    result = await mock_repo.add_item(return_id=1, item=item)

    assert result == return_tx
    assert existing_line.quantity == 5 

    mock_session.add.assert_not_called()  
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(return_tx)
