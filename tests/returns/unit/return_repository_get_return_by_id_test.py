from unittest.mock import AsyncMock, MagicMock
import pytest
from app.models.DAO.return_dao import ReturnDAO
from app.models.errors.notfound_error import NotFoundError
from app.repositories.return_repository import ReturnRepository

@pytest.mark.asyncio
async def test_get_return_by_id_empty():
    # Repository creation
    repo = ReturnRepository()

    # Mock of DB session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()

    # Mock of query result
    mock_result = MagicMock()
    # Setting scalars().first() to return None
    mock_result.scalars.return_value.first.return_value = None

    # Setting the session's execute to return the mock result
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Injecting mock session into repository -> "When out db ask for a session, give it the mock session"
    repo._get_session = AsyncMock(return_value = mock_session)

    with pytest.raises(NotFoundError):
        result = await repo.get_return_by_id(1)
        
        # Assert that result is None
        assert result == None


@pytest.mark.asyncio
async def test_get_return_by_id_success():
    # Repository creation
    repo = ReturnRepository()

    # Mock of DB session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()

    # Mock of query result
    mock_result = MagicMock()

    # Creating mock return transactions
    fake_return = MagicMock(spec=ReturnDAO)

    # Setting scalars().first() to return the fake return
    mock_result.scalars.return_value.first.return_value = fake_return

    # Setting the session's execute to return the mock result
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Injecting mock session into repository -> "When out db ask for a session, give it the mock session"
    repo._get_session = AsyncMock(return_value = mock_session)

    # Call to get_return_by_id
    result = await repo.get_return_by_id(1)

    # Assert that result is the fake return
    assert result == fake_return
    assert isinstance(result, ReturnDAO)

    mock_session.execute.assert_awaited_once()
    mock_result.scalars.assert_called_once()
    mock_result.scalars.return_value.first.assert_called_once()