from unittest.mock import AsyncMock, MagicMock
import pytest
from app.models.DAO.return_dao import ReturnDAO
from app.repositories.return_repository import ReturnRepository

@pytest.mark.asyncio
async def test_get_return_by_sale_id_empty():
    repo = ReturnRepository()
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    repo._get_session = AsyncMock(return_value=mock_session)

    mock_returns = []

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_result.scalars.return_value = mock_scalars
    mock_scalars.all.return_value = mock_returns

    result = await repo.get_returns_by_sale(sale_id=100)

    assert result == mock_returns
    assert len(result) == 0
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_returns_by_sale_success():
    repo = ReturnRepository()
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    repo._get_session = AsyncMock(return_value=mock_session)

    mock_returns = [
        ReturnDAO(id=1, sale_id=100, status="CLOSED"),
        ReturnDAO(id=2, sale_id=100, status="CLOSED"),
    ]

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_result.scalars.return_value = mock_scalars
    mock_scalars.all.return_value = mock_returns

    result = await repo.get_returns_by_sale(sale_id=100)

    assert result == mock_returns
    assert len(result) == 2
    assert result[0].sale_id == 100
    mock_session.execute.assert_called_once()