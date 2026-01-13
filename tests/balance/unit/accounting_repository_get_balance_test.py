from unittest.mock import AsyncMock, MagicMock
import pytest
from app.models.DAO.system_dao import SystemInfoDAO
from app.repositories.system_repository import SystemRepository

@pytest.fixture
def mock_session():
    """Create a properly configured mock session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_repo(mock_session):
    """Create a repository with mocked session context manager."""
    repo = SystemRepository()
    
    # Create a mock context manager that returns mock_session
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    
    # get_session() should return the context manager
    repo.get_session = MagicMock(return_value=mock_context_manager)
    
    # Store context manager for test verification
    repo._mock_context_manager = mock_context_manager
    return repo

@pytest.mark.asyncio
async def test_get_balance_with_success(mock_repo, mock_session):
    """Test retrieving system balance successfully."""
    expected_balance = 1500.0
    
    # Mock the query to return a SystemInfoDAO with expected balance
    mock_system_info = SystemInfoDAO(balance=expected_balance)
    mock_scalars = MagicMock()  # scalars() is sync
    mock_scalars.first = MagicMock(return_value=mock_system_info)
    mock_query = MagicMock()  # result object from execute() is sync
    mock_query.scalars = MagicMock(return_value=mock_scalars)
    mock_session.execute = AsyncMock(return_value=mock_query)  # execute() is async
    
    result = await mock_repo.get_last_system_info()

    assert isinstance(result, SystemInfoDAO)
    assert result.balance == expected_balance
    
    # Verify session.execute was awaited
    mock_session.execute.assert_awaited_once()
    
    # Verify get_session was called once
    mock_repo.get_session.assert_called_once()
    
    # Verify context manager was entered and exited
    mock_repo._mock_context_manager.__aenter__.assert_called_once()
    mock_repo._mock_context_manager.__aexit__.assert_called_once()

@pytest.mark.asyncio
async def test_get_balance_no_system_info(mock_repo, mock_session):
    """Test retrieving system balance when no system info exists."""
    
    # Mock the query to return None
    mock_scalars = MagicMock()  # scalars() is sync
    mock_scalars.first = MagicMock(return_value=None)
    mock_query = MagicMock()  # result object from execute() is sync
    mock_query.scalars = MagicMock(return_value=mock_scalars)
    mock_session.execute = AsyncMock(return_value=mock_query)  # execute() is async
    
    result = await mock_repo.get_last_system_info()

    assert result is None
    
    # Verify session.execute was awaited
    mock_session.execute.assert_awaited_once()
    
    # Verify get_session was called once
    mock_repo.get_session.assert_called_once()
    
    # Verify context manager was entered and exited
    mock_repo._mock_context_manager.__aenter__.assert_called_once()
    mock_repo._mock_context_manager.__aexit__.assert_called_once()

@pytest.mark.asyncio
async def test_get_balance_session_error(mock_repo, mock_session):
    """Test retrieving system balance when session raises an error."""
    
    # Mock session.execute to raise an exception
    mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
    
    with pytest.raises(Exception) as exc_info:
        await mock_repo.get_last_system_info()
    
    assert str(exc_info.value) == "Database error"
    
    # Verify session.execute was awaited
    mock_session.execute.assert_awaited_once()
    
    # Verify get_session was called once
    mock_repo.get_session.assert_called_once()
    
    # Verify context manager was entered and exited
    mock_repo._mock_context_manager.__aenter__.assert_called_once()
    mock_repo._mock_context_manager.__aexit__.assert_called_once()