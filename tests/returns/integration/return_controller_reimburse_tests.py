import asyncio
from datetime import datetime
import pytest
import pytest_asyncio
from app.database.database import  AsyncSessionLocal, get_db, init_db, reset_db, AsyncSession
from app.controllers.return_controller import ReturnController
from app.models.DAO.sale_dao import SaleDAO
from app.models.DAO.return_dao import ReturnDAO, ReturnLineDAO
from app.models.DAO.system_dao import SystemInfoDAO
from app.models.DTO.return_dto import ReturnDTO, ReturnItemDTO, ReturnReimburseDTO
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
async def instance_of_return_not_closed():
    async with await _get_session() as session:
        system = SystemInfoDAO(balance=1000)
        session.add(system)
        await session.commit()
        await session.refresh(system)
        sale1 = SaleDAO(status="PAID")
        session.add(sale1)
        await session.commit()
        await session.refresh(sale1)
        return1 = ReturnDAO(sale_id=sale1.id, status="OPEN")
        session.add(return1)
        await session.commit()
        await session.refresh(return1)
        line1 = ReturnLineDAO(return_id = return1.id, product_barcode="ABC123", quantity=2, price_per_unit=10.0)
        session.add(line1)
        await session.commit()
        await session.refresh(line1)
        return return1

    
@pytest_asyncio.fixture
async def instance_of_closed_return():
    async with await _get_session() as session:
        system = SystemInfoDAO(balance=1000)
        session.add(system)
        await session.commit()
        await session.refresh(system)
        sale1 = SaleDAO(status="PAID")
        session.add(sale1)
        await session.commit()
        await session.refresh(sale1)
        return1 = ReturnDAO(sale_id=sale1.id, status="CLOSED")
        session.add(return1)
        await session.commit()
        await session.refresh(return1)
        line1 = ReturnLineDAO(return_id = return1.id, product_barcode="ABC123", quantity=2, price_per_unit=10.0)
        session.add(line1)
        await session.commit()
        await session.refresh(line1)
        return return1
    
@pytest.mark.asyncio
async def test_reimburse_not_found():
    # Controller creation
    controller = ReturnController()

    with pytest.raises(NotFoundError):
        result = await controller.reimburse_return(return_id=1)

        assert result is None


@pytest.mark.asyncio
async def test_reimburse_invalid_state(instance_of_return_not_closed):
    # Controller creation
    controller = ReturnController()

    with pytest.raises(InvalidStateError):
        result = await controller.reimburse_return(return_id=instance_of_return_not_closed.id)

        assert result is None


@pytest.mark.asyncio
async def test_reimburse_success(instance_of_closed_return):
    # Controller creation
    controller = ReturnController()

    result = await controller.reimburse_return(return_id=instance_of_closed_return.id)

    assert isinstance(result, ReturnReimburseDTO)
    assert result.refund_amount == 20
