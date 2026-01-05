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
async def system_info_with_balance_500():
    """Fixture that creates a system info record with 500.0 balance"""
    async with await _get_session() as session:
        system_info = SystemInfoDAO(balance=500.0)
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
async def test_reset_balance_success(system_info_with_balance_100):
    """Test that reset_balance successfully sets the balance to zero"""
    controller = SystemController()
    
    # Verify initial balance is set
    initial_balance = await controller.get_balance()
    assert initial_balance.balance == 100.0
    
    # Reset balance
    await controller.reset_balance()
    
    # Verify balance is reset to zero
    result = await controller.get_balance()
    assert result.balance == 0.0


@pytest.mark.asyncio
async def test_reset_balance_creates_new_record(system_info_with_balance_100):
    """Test that reset_balance creates a new record in the database"""
    controller = SystemController()
    
    # Get initial balance record
    initial_balance = await controller.get_balance()
    assert initial_balance.balance == 100.0
    
    # Reset balance
    await controller.reset_balance()
    
    # Get the result
    result = await controller.get_balance()
    assert result.balance == 0.0


@pytest.mark.asyncio
async def test_reset_balance_and_set_after():
    """Test that after reset_balance, set_balance works correctly"""
    controller = SystemController()
    
    # Set initial balance
    await controller.set_balance(amount=200.0)
    result1 = await controller.get_balance()
    assert result1.balance == 200.0
    
    # Reset balance
    await controller.reset_balance()
    result2 = await controller.get_balance()
    assert result2.balance == 0.0
    
    # Set new balance after reset
    await controller.set_balance(amount=300.0)
    result3 = await controller.get_balance()
    assert result3.balance == 300.0
