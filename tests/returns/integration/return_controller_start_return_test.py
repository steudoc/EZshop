import asyncio
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
async def sale_paid():
    async with await _get_session() as session:
        sale = SaleDAO(status="PAID")
        session.add(sale)
        await session.commit()
        await session.refresh(sale)
        return sale

@pytest_asyncio.fixture
async def sale_open():
    async with await _get_session() as session:
        sale = SaleDAO(status="OPEN")
        session.add(sale)
        await session.commit()
        await session.refresh(sale)
        return sale

@pytest.mark.asyncio
async def test_start_return_not_found():
    controller = ReturnController()
    
    with pytest.raises(NotFoundError):
        result = await controller.start_return(sale_id=1)
        assert result is None


@pytest.mark.asyncio
async def test_start_return_invalid_sale(sale_open):
    controller = ReturnController()
    
    with pytest.raises(InvalidStateError):
        result = await controller.start_return(sale_id=sale_open.id)
        assert result is None


@pytest.mark.asyncio
async def test_start_return_success(sale_paid):
    controller = ReturnController()

    result = await controller.start_return(sale_id=sale_paid.id)

    assert isinstance(result, ReturnDTO)
    assert result.sale_id == sale_paid.id
    assert result.status == "OPEN"