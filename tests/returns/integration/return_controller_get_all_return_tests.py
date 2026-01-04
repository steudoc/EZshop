import asyncio
from datetime import datetime
import pytest
import pytest_asyncio
from app.database.database import  AsyncSessionLocal, get_db, init_db, reset_db, AsyncSession
from app.controllers.return_controller import ReturnController
from app.models.DAO.sale_dao import SaleDAO
from app.models.DAO.return_dao import ReturnDAO
from app.models.DTO.return_dto import ReturnDTO
from app.models.errors.invalidstate_error import InvalidStateError
from app.models.errors.notfound_error import NotFoundError



@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database(event_loop):
    async def _reset():
        await reset_db() # Dropp all tables
        await init_db() # Recreate all tables
    event_loop.run_until_complete(_reset())

async def _get_session() -> AsyncSession:
        return AsyncSessionLocal()

@pytest_asyncio.fixture
async def list_of_returns():
    async with await _get_session() as session:
        returns = []

        
        sale1 = SaleDAO(status="PAID")
        session.add(sale1)
        await session.commit()
        await session.refresh(sale1)
        return1 = ReturnDAO(sale_id=sale1.id, status="OPEN")
        session.add(return1)
        await session.commit()
        await session.refresh(return1)

        returns.append(return1)

        sale2 = SaleDAO(status="PAID")
        session.add(sale2)
        await session.commit()
        await session.refresh(sale2)
        return2 = ReturnDAO(sale_id=sale2.id, status="CLOSED", closed_at=datetime.now())
        session.add(return2)
        await session.commit()
        await session.refresh(return2)

        returns.append(return2)

        sale3 = SaleDAO(status="PAID")
        session.add(sale3)
        await session.commit()
        await session.refresh(sale3)
        return3 = ReturnDAO(sale_id=sale3.id, status="OPEN")
        session.add(return3)
        await session.commit()
        await session.refresh(return3)

        returns.append(return3)

        return returns

@pytest.mark.asyncio
async def test_get_all_returns_empty():
    # Controller creation
    controller = ReturnController()

    # Call to get_all_returns
    result = await controller.get_all_returns()

    # Assert that result is an empty list
    assert result == []





@pytest.mark.asyncio
async def test_get_all_returns_non_empty(list_of_returns):
    # Controller creation
    controller = ReturnController()

    # Call to get_all_returns
    result = await controller.get_all_returns()

    # Assert that result contains the three returns
    assert len(result) == 3

    # Assert that all items in result are instances of ReturnDTO
    assert all(isinstance(r, ReturnDTO) for r in result)