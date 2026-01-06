import asyncio
import pytest
import pytest_asyncio
from app.database.database import AsyncSessionLocal, get_db, init_db, reset_db, AsyncSession
from app.controllers.system_controller import SystemController
from app.models.DAO.system_dao import SystemInfoDAO
from app.models.errors.balance_error import BalanceError
from app.models.errors.notfound_error import NotFoundError


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database(event_loop):
    async def _reset():
        await reset_db()  # Drop all tables
        await init_db()   # Recreate all tables
    event_loop.run_until_complete(_reset())
    yield
    event_loop.run_until_complete(_reset())


async def _get_session() -> AsyncSession:
    return AsyncSessionLocal()


@pytest_asyncio.fixture
async def system_info_with_balance_100():
    """Fixture that creates a system info record with 100.0 balance"""
    async with await _get_session() as session:
        system_info = SystemInfoDAO(balance=100.0)
        session.add(system_info)
        await session.commit()
        await session.refresh(system_info)
        return system_info


@pytest_asyncio.fixture
async def system_info_with_balance_zero():
    """Fixture that creates a system info record with zero balance"""
    async with await _get_session() as session:
        system_info = SystemInfoDAO(balance=0.0)
        session.add(system_info)
        await session.commit()
        await session.refresh(system_info)
        return system_info


@pytest_asyncio.fixture
async def system_info_with_balance_large():
    """Fixture that creates a system info record with a large balance"""
    async with await _get_session() as session:
        system_info = SystemInfoDAO(balance=999999.99)
        session.add(system_info)
        await session.commit()
        await session.refresh(system_info)
        return system_info


@pytest.mark.asyncio
async def test_get_balance_success(system_info_with_balance_100):
    """Test that get_balance returns the current balance successfully"""
    controller = SystemController()
    
    result = await controller.get_balance()
    
    assert result.balance == 100.0
    assert hasattr(result, 'balance')


@pytest.mark.asyncio
async def test_get_balance_zero_value(system_info_with_balance_zero):
    """Test that get_balance returns zero balance correctly"""
    controller = SystemController()
    
    result = await controller.get_balance()
    
    assert result.balance == 0.0


@pytest.mark.asyncio
async def test_get_balance_not_found():
    """Test that get_balance raises NotFoundError when no balance is set"""
    controller = SystemController()
    
    with pytest.raises(NotFoundError):
        await controller.get_balance()
