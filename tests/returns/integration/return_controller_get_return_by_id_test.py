import asyncio
from datetime import datetime
import pytest
import pytest_asyncio
from app.database.database import  AsyncSessionLocal, init_db, reset_db, AsyncSession
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
async def instance_of_return():
    async with await _get_session() as session:
        
        sale1 = SaleDAO(status="PAID")
        session.add(sale1)
        await session.commit()
        await session.refresh(sale1)
        return1 = ReturnDAO(sale_id=sale1.id, status="OPEN")
        session.add(return1)
        await session.commit()
        await session.refresh(return1)

        return return1

@pytest.mark.asyncio
async def test_get_return_by_id_empty():
    # Controller creation
    controller = ReturnController()

    with pytest.raises(NotFoundError):
        result = await controller.get_return_by_id(return_id=1)
        
        # Assert that result is None
        assert result == None


@pytest.mark.asyncio
async def test_get_return_by_id_success(instance_of_return):
    # Controller creation
    controller = ReturnController()

    # Call to get_return_by_id
    result = await controller.get_return_by_id(return_id=instance_of_return.id)

    assert result.closed_at == instance_of_return.closed_at
    assert result.id == instance_of_return.id
    assert result.sale_id == instance_of_return.sale_id
    assert result.status == instance_of_return.status
    assert isinstance(result, ReturnDTO)
