from unittest.mock import AsyncMock, MagicMock
import pytest
from app.models.DAO.return_dao import ReturnDAO
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError
from app.repositories.return_repository import ReturnRepository
from app.models.sale_status import SaleStatus

@pytest.mark.asyncio
async def test_start_return_invalid_sale():
    # Create repository instance with mocked session
    service = ReturnRepository()
    # Create mock session
    mock_session = AsyncMock()
    # Create mock sale
    sale = MagicMock()

    mock_session.get.return_value = sale
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    service._get_session = AsyncMock(return_value=mock_session)

    with pytest.raises(InvalidStateError):
            await service.start_return(1)

@pytest.mark.asyncio
async def test_start_return_not_found():
    # Create repository instance with mocked session
    service = ReturnRepository()
    mock_session = AsyncMock()


    mock_session.get.return_value = None
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    service._get_session = AsyncMock(return_value=mock_session)

    # Attempt to start return for non-existing sale
    with pytest.raises(NotFoundError):
            await service.start_return(1)


@pytest.mark.asyncio
async def test_start_return_success():
    service = ReturnRepository()
    mock_session = MagicMock()

    # async methods
    mock_session.get = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # sync method
    mock_session.add = MagicMock()

    sale = MagicMock()
    sale.status = SaleStatus.PAID
    
    mock_session.get.return_value = sale
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    service._get_session = AsyncMock(return_value=mock_session)

    result = await service.start_return(1)

    assert isinstance(result, ReturnDAO)
    assert result.sale_id == 1
    assert result.status == "OPEN"
    
    # Check that the return transaction is added to the session
    mock_session.add.assert_called_once_with(result)

    # Check that the changes are committed to the database
    mock_session.commit.assert_awaited()

    # Check that the return transaction is refreshed before being returned
    mock_session.refresh.assert_awaited_with(result)

