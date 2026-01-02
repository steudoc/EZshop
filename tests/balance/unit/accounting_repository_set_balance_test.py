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
async def test_create_system_info_decimal_precision(mock_repo, mock_session):
    """Test decimal precision is maintained."""
    balance = 1234.567
    
    result = await mock_repo.create_system_info(balance=balance)

    assert result.balance == balance
    added_dao = mock_session.add.call_args[0][0]
    assert added_dao.balance == balance


@pytest.mark.asyncio
async def test_create_system_info_multiple_calls(mock_repo, mock_session):
    """Test multiple calls to create_system_info."""
    balances = [1000.0, 2000.0, 3000.0]
    
    for balance in balances:
        await mock_repo.create_system_info(balance=balance)

    # Verify add, flush, refresh were called 3 times each
    assert mock_session.add.call_count == 3
    assert mock_session.flush.call_count == 3
    assert mock_session.refresh.call_count == 3


@pytest.mark.asyncio
async def test_create_system_info_session_context_manager(mock_repo, mock_session):
    """Test that get_session context manager is properly used."""
    balance = 5000.0
    
    await mock_repo.create_system_info(balance=balance)

    # Verify get_session was called once
    mock_repo.get_session.assert_called_once()
    
    # Verify context manager was entered and exited
    mock_repo._mock_context_manager.__aenter__.assert_called_once()
    mock_repo._mock_context_manager.__aexit__.assert_called_once()








