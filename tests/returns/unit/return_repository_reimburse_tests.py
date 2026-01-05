import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.DAO.return_dao import ReturnDAO
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError
from app.repositories.return_repository import ReturnRepository

@pytest.fixture
def mock_session():
    session = AsyncMock()
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
async def test_reimburse_not_found(mock_repo, mock_session):
    mock_session.get.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        result = await mock_repo.reimburse_return(return_id=1)

        assert result is None

    mock_session.get.assert_awaited_once_with(ReturnDAO, 1)


@pytest.mark.asyncio
async def test_reimburse_invalid_state(mock_repo, mock_session):
    mock_session.get.return_value = ReturnDAO(id=1, sale_id=100, status="OPEN")

    with pytest.raises(InvalidStateError) as exc_info:
        result = await mock_repo.reimburse_return(return_id=1)

        assert result is None

    mock_session.get.assert_awaited_once_with(ReturnDAO, 1)

@pytest.mark.asyncio
async def test_reimburse_success(mock_repo, mock_session):
    mock_return = ReturnDAO(id=1, sale_id=100, status="CLOSED")
    mock_session.get.return_value = mock_return

    result = await mock_repo.reimburse_return(return_id=1)

    assert result == mock_return

    mock_session.get.assert_awaited_once_with(ReturnDAO, 1)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(mock_return)