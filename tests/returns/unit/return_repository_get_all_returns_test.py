from unittest.mock import AsyncMock, MagicMock
import pytest
from app.models.DAO.return_dao import ReturnDAO
from app.repositories.return_repository import ReturnRepository

@pytest.mark.asyncio
async def test_get_all_returns_empty():
    # Repository creation
    repo = ReturnRepository()

    # Mock of DB session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()

    # Mock of query result
    mock_result = MagicMock()
    # Setting scalars().all() to return empty list
    mock_result.scalars.return_value.all.return_value = []

    # Setting the session's execute to return the mock result
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Injecting mock session into repository -> "When out db ask for a session, give it the mock session"
    repo._get_session = AsyncMock(return_value = mock_session)

    # Call to get_all_returns
    result = await repo.get_all_returns()

    # Assert that result is an empty list
    assert result == []



@pytest.mark.asyncio
async def test_get_all_returns_non_empty():
    # Repository creation
    repo = ReturnRepository()

    # Mock of DB session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()

    # Mock of query result
    mock_result = MagicMock()

    # Creating mock return transactions
    return1 = MagicMock(spec=ReturnDAO)
    return2 = MagicMock(spec=ReturnDAO)

    # Setting scalars().all() to return list with two mock returns
    mock_result.scalars.return_value.all.return_value = [return1, return2]

    # Setting the session's execute to return the mock result
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Injecting mock session into repository -> "When out db ask for a session, give it the mock session"
    repo._get_session = AsyncMock(return_value = mock_session)

    # Call to get_all_returns
    result = await repo.get_all_returns()

    # Assert that result contains the two mock returns
    assert len(result) == 2

    # Assert that all items in result are instances of ReturnDAO
    assert all(isinstance(r, ReturnDAO) for r in result)

    mock_session.execute.assert_awaited_once()
    mock_result.scalars.assert_called_once()
    mock_result.scalars.return_value.all.assert_called_once()
