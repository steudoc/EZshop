from unittest.mock import AsyncMock, MagicMock
import pytest
from app.models.DAO.return_dao import ReturnDAO
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError
from app.repositories.return_repository import ReturnRepository

@pytest.mark.asyncio
async def test_delete_reimbursed_return():
    # Create repository instance with mocked session
    repo = ReturnRepository()
    # Create mock session
    mock_session = AsyncMock()
    # Create mock sale
    sale = MagicMock()
    sale.status = "REIMBURSED"

    mock_session.get.return_value = sale
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    repo._get_session = AsyncMock(return_value=mock_session)

    with pytest.raises(InvalidStateError):
            await repo.delete_return(1)

@pytest.mark.asyncio
async def test_delete_return_not_found():
    # Create repository instance with mocked session
    repo = ReturnRepository()
    # Create mock session
    mock_session = AsyncMock()

    mock_session.get.return_value = None
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    repo._get_session = AsyncMock(return_value=mock_session)

    with pytest.raises(NotFoundError):
            await repo.delete_return(1)


@pytest.mark.asyncio
async def test_delete_return_success():
    # Create repository instance with mocked session
    repo = ReturnRepository()
    # Create mock session
    mock_session = AsyncMock()

    # async methods
    mock_session.get = AsyncMock()
    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock()

    sale = MagicMock()
    sale.status = "CLOSED"
    
    mock_session.get.return_value = sale
    mock_session.__aenter__.return_value = mock_session
    repo._get_session = AsyncMock(return_value=mock_session)

    result = await repo.delete_return(return_id=1)
    mock_session.get.assert_called_once_with(ReturnDAO, 1)
    mock_session.delete.assert_called_once_with(sale)
    mock_session.commit.assert_called_once()
    assert result is True