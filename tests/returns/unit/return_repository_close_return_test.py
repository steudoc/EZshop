from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.DAO.return_dao import ReturnDAO
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
async def test_close_return_not_found(mock_repo, mock_session):
    mock_session.get.return_value = None

    result = await mock_repo.close_return(1)

    assert result is None

    mock_session.get.assert_awaited_once_with(ReturnDAO, 1)
    mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_close_return_success(mock_repo, mock_session, monkeypatch):
    fixed_now = datetime(2024, 1, 1, 12, 0, 0)

    def mock_now():
        return fixed_now

    # patch del datetime USATO nel modulo
    monkeypatch.setattr(
        "app.repositories.return_repository.datetime",
        MagicMock(now=mock_now)
    )
    
    mock_return_tx = MagicMock(spec=ReturnDAO)
    mock_return_tx.status = "OPEN"
    mock_return_tx.closed_at = None

    mock_session.get=AsyncMock(return_value=mock_return_tx)

    result = await mock_repo.close_return(1)

    assert result == mock_return_tx
    assert mock_return_tx.status == "CLOSED"
    assert mock_return_tx.closed_at == fixed_now

    mock_session.get.assert_awaited_once_with(ReturnDAO, 1)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(mock_return_tx)