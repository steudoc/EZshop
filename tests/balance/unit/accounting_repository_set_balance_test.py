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
async def test_create_system_info_success(mock_repo, mock_session):
    """Test creating system info with positive balance."""
    balance = 1000.0
    
    result = await mock_repo.create_system_info(balance=balance)

    assert isinstance(result, SystemInfoDAO)
    assert result.balance == balance
    
    # Verify session.add was called with a SystemInfoDAO
    mock_session.add.assert_called_once()
    added_dao = mock_session.add.call_args[0][0]
    assert isinstance(added_dao, SystemInfoDAO)
    assert added_dao.balance == balance

    # Verify session.flush was awaited
    mock_session.flush.assert_awaited_once()

    # Verify session.refresh was awaited
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_system_info_zero_balance(mock_repo, mock_session):
    """Test creating system info with zero balance."""
    balance = 0.0
    
    result = await mock_repo.create_system_info(balance=balance)

    assert result.balance == 0.0
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_system_info_negative_balance(mock_repo, mock_session):
    """Test creating system info with negative balance (repo doesn't validate)."""
    balance = -100.0
    
    result = await mock_repo.create_system_info(balance=balance)

    # Repository accepts it - validation is controller's responsibility
    assert result.balance == balance
    mock_session.add.assert_called_once()

@pytest.mark.asyncio
async def test_create_system_info_failure(mock_repo, mock_session):
    """Test handling of session failure during create_system_info."""
    balance = 500.0
    
    # Configure session.add to raise an exception
    mock_session.add.side_effect = Exception("Database error")
    
    with pytest.raises(Exception) as exc_info:
        await mock_repo.create_system_info(balance=balance)
    
    assert str(exc_info.value) == "Database error"
    
    # Verify session.add was called
    mock_session.add.assert_called_once()








