import asyncio
import pytest
from app.controllers.card_controller import CardController
from app.models.DAO.card_dao import CardDAO
from app.models.DAO.customer_dao import CustomerDAO
from app.services.mapper_service import carddao_to_response_dto, customerdao_to_responsedto
from main import app
from init_db import reset, init_db
import app.database.database as db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# ---------------------------
# LOCAL FIXTURE FOR RESETTING DB
# ---------------------------

@pytest.fixture(autouse=True)
def reset_db_but_keep_users(event_loop):
    """Fixture to execute asserts before and after a test is run"""
    # reset db and ensure users are back 
    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())

    yield
    # nothing after tests are done
    
# some helper functions that work with db (they do not include 
# most checks because they assume valid inputs)


async def create_two_customers() -> tuple[CustomerDAO, CustomerDAO]:
	customer = None
	customer_1 = None

	# create two customers
	async with db.AsyncSessionLocal() as session:
		customer = CustomerDAO(name = "Marco Bianchi")
		customer_1 = CustomerDAO(name = "Paolo Rossi")
		session.add(customer)
		session.add(customer_1)
		await session.commit()

	return (customer, customer_1)


async def create_card(points_amount = 0) -> CardDAO:
	create_card = None
	# create card with given points
	async with db.AsyncSessionLocal() as session:
		create_card = CardDAO(points = points_amount)
		session.add(create_card)

		await session.commit()

	return create_card


async def attach_card(customer_id, card_id) -> None:
	async with db.AsyncSessionLocal() as session:
		card = await session.get(CardDAO, card_id)
		card.customer_id = customer_id
		await session.commit()
		await session.refresh(card)


# -----------------------------------------
# CARD DAO TO RESPONSE DTO TESTS
# -----------------------------------------

@pytest.mark.asyncio
async def test_card_dato_to_response_dto():
      
	# create a dao, get the dto and check they have the same data
	card_dao = await create_card(0)
	card_dto = carddao_to_response_dto(card_dao)
		
	assert card_dto.card_id == card_dao.cardId
	assert card_dto.points == card_dao.points
		
	# create a dao, get the dto and check they have the same data
	card_dao = await create_card(1000)
	card_dto = carddao_to_response_dto(card_dao)
		
	assert card_dto.card_id == card_dao.cardId
	assert card_dto.points == card_dao.points

# ------------------------------------------
# CUSTOMER DAO TO RESPONSE DTO TESTS
# ------------------------------------------

# TODO: ensure expected is None and not error

@pytest.mark.asyncio
async def test_customer_dao_to_response_dto():
	customer_dao, customer_dao_1 = await create_two_customers() 
	card_dao = await create_card()

	await attach_card(customer_dao_1.id, card_dao.cardId)

	customer_dto = await customerdao_to_responsedto(customer_dao)
	customer_dto_1 = await customerdao_to_responsedto(customer_dao_1)

	# ensure customer has the correct data
	assert customer_dto.id == customer_dao.id
	assert customer_dto.name == customer_dao.name
	assert customer_dto.card is None

	# ensure customer 1 has the correct data and correct card data
	assert customer_dto_1.id == customer_dao_1.id
	assert customer_dto_1.name == customer_dao_1.name
	assert customer_dto_1.card is not None
	assert customer_dto_1.card.card_id == card_dao.cardId
	assert customer_dto_1.card.points == card_dao.points




