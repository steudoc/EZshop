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
async def system_info_with_balance():
    """Fixture that creates a system info record with a specific balance"""
    async with await _get_session() as session:
        system_info = SystemInfoDAO(balance=100.0)
        session.add(system_info)
        await session.commit()
        await session.refresh(system_info)
        return system_info


@pytest_asyncio.fixture
async def system_info_zero_balance():
    """Fixture that creates a system info record with zero balance"""
    async with await _get_session() as session:
        system_info = SystemInfoDAO(balance=0.0)
        session.add(system_info)
        await session.commit()
        await session.refresh(system_info)
        return system_info


@pytest.mark.asyncio
async def test_set_balance_success():
    """Test that set_balance successfully sets a positive balance"""
    controller = SystemController()
    
    await controller.set_balance(amount=250.50)
    
    result = await controller.get_balance()
    assert result.balance == 250.50


@pytest.mark.asyncio
async def test_set_balance_zero():
    """Test that set_balance can set balance to zero"""
    controller = SystemController()
    
    await controller.set_balance(amount=0.0)
    
    result = await controller.get_balance()
    assert result.balance == 0.0


@pytest.mark.asyncio
async def test_set_balance_negative_raises_error():
    """Test that set_balance raises BalanceError when amount is negative"""
    controller = SystemController()
    
    with pytest.raises(BalanceError):
        await controller.set_balance(amount=-100.0)


@pytest.mark.asyncio
async def test_set_balance_overwrites_previous():
    """Test that set_balance overwrites the previous balance"""
    controller = SystemController()
    
    await controller.set_balance(amount=100.0)
    result1 = await controller.get_balance()
    assert result1.balance == 100.0
    
    await controller.set_balance(amount=500.75)
    result2 = await controller.get_balance()
    assert result2.balance == 500.75


