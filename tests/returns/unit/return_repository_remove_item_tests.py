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
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    return session


@pytest.fixture
def mock_repo(mock_session):
    repo = ReturnRepository()
    repo._get_session = AsyncMock()
    repo._get_session.return_value.__aenter__.return_value = mock_session
    repo._get_session.return_value.__aexit__.return_value = None
    return repo

@pytest.mark.asyncio
async def test_remove_item_return_not_found(mock_repo, mock_session):

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(NotFoundError):
        await mock_repo.remove_item(return_id=99, product_barcode="ABC123", quantity=1)

    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()



@pytest.mark.asyncio
async def test_remove_item_success_delete(mock_repo, mock_session):

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = ReturnLineDAO(
        id=1,
        return_id=1,
        product_barcode="ABC123",
        quantity=2,
        price_per_unit=10.0
    )
    mock_session.execute.return_value = mock_result
    
    return_tx = MagicMock(spec=ReturnDAO)
    mock_session.get.return_value = return_tx

    result = await mock_repo.remove_item(return_id=1, product_barcode="ABC123", quantity=2)

    mock_session.delete.assert_awaited_once()
    mock_session.commit.assert_awaited_once()
    
    assert result == return_tx

    mock_session.get.assert_awaited_once_with(
        ReturnDAO,
        1,
        options=ANY
    )


@pytest.mark.asyncio
async def test_remove_item_success_decrease(mock_repo, mock_session):

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = ReturnLineDAO(
        id=1,
        return_id=1,
        product_barcode="ABC123",
        quantity=2,
        price_per_unit=10.0
    )
    mock_session.execute.return_value = mock_result
    
    return_tx = MagicMock(spec=ReturnDAO)
    mock_session.get.return_value = return_tx

    result = await mock_repo.remove_item(return_id=1, product_barcode="ABC123", quantity=1)

    mock_session.delete.assert_not_called()
    mock_session.commit.assert_awaited_once()

    assert result == return_tx

    mock_session.get.assert_awaited_once_with(
        ReturnDAO,
        1,
        options=ANY
    )

    # TODO : remove function delete line in each scenario
    # when quantity is less than existing line quantity 
    # we should just decrease the quantity instead of 
    # deleting the line