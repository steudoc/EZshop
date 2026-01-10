import asyncio
import pytest
from sqlalchemy import select
from app.models.DAO.card_dao import CardDAO
from app.models.DAO.customer_dao import CustomerDAO
from app.models.DTO.customer_dto import CardDTO, UpdateCardDTO
from app.models.errors.bad_request import BadRequestError
from app.models.errors.conflict_error import ConflictError
from app.models.errors.notfound_error import NotFoundError
from app.repositories.customer_repository import CustomerRepository
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
async def create_customer(customer_name = "Marco Bianchi") ->CustomerDAO:
	customer = None

	# create two customers
	async with db.AsyncSessionLocal() as session:
		customer = CustomerDAO(name = customer_name)
		session.add(customer)
		await session.commit()

	return customer


async def create_card() -> CardDAO:
	create_card = None
	# create card
	async with db.AsyncSessionLocal() as session:
		create_card = CardDAO(points = 0)
		session.add(create_card)

		await session.commit()

	return create_card


async def attach_card(customer_id, card_id) -> None:
	async with db.AsyncSessionLocal() as session:
		card = await session.get(CardDAO, card_id)
		card.customer_id = customer_id
		await session.commit()
		await session.refresh(card)


async def get_card_by_customer(customer_id: int) -> CardDAO | None:
	async with db.AsyncSessionLocal() as session:
		result = await session.execute(select(CardDAO).filter_by(customer_id=customer_id))
		return result.scalars().first()
        

async def get_card_by_id(card_id: int) -> CardDAO | None:
	async with db.AsyncSessionLocal() as session:
		result = await session.execute(select(CardDAO).filter_by(cardId=card_id))
		return result.scalars().first()

async def get_customer_by_id(customer_id: int) -> CardDAO | None:
	async with db.AsyncSessionLocal() as session:
		result = await session.execute(select(CustomerDAO).filter_by(id=customer_id))
		return result.scalars().first()


# ---------------------------
# CREATE CUSTOMER TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_create_customer():
	customer_repo = CustomerRepository()

	customer_name = "Marco Bianchi"
	created_card = await create_card()
	card_dto = carddao_to_response_dto(created_card)

	# create a customer without a card
	customer, card = await customer_repo.create_customer(customer_name, None)
	assert customer is not None
	assert customer.name == customer_name
	assert card is None

	# create a customer with a card
	customer_1, card = await customer_repo.create_customer(customer_name, card_dto)
	assert customer is not None
	assert customer.name == customer_name
	assert card is not None
	assert card.cardId == created_card.cardId
	assert card.customer_id == customer_1.id

	# create a customer with a card that is already assigned
	# (use same card as before, so it should raise an error)
	with pytest.raises(ConflictError):
		customer_2, card = await customer_repo.create_customer(
			customer_name, card_dto)


# ---------------------------
# GET CUSTOMER TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_get_customer_success():
	customer_repo = CustomerRepository()
	
	# create a customer
	created_customer = await create_customer()

	# search for the created customer
	customer = await customer_repo.get_customer(created_customer.id)
	assert customer is not None
	assert customer.name == created_customer.name
	assert customer.id == created_customer.id


@pytest.mark.asyncio
async def test_get_customer_not_found():
	customer_repo = CustomerRepository()

	# search for a customer that does not exist
	with pytest.raises(NotFoundError):
		customer = await customer_repo.get_customer(-1)

	# search for a customer that does not exist
	with pytest.raises(NotFoundError):
		customer = await customer_repo.get_customer(9999)


# ---------------------------
# LIST CUSTOMERS TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_list_customers_empty():
	customer_repo = CustomerRepository()

	# list customers should return empty list
	empty_list = await customer_repo.list_customers()
	assert empty_list is not None
	assert empty_list == []


@pytest.mark.asyncio
async def test_list_customers_success():
	customer_repo = CustomerRepository()

	# create two customers
	created_customer = await create_customer("Paolo Rossi")
	created_customer_1 = await create_customer("Giorgio Neri")

	# list customers should contain both customers
	customers_list = await customer_repo.list_customers()
	assert customers_list is not None
	assert len(customers_list) == 2

	# first customer in first position
	if (customers_list[0].name == created_customer.name):
		assert customers_list[1].name == created_customer_1.name
	# first customer in second position
	else:
		assert customers_list[0].name == created_customer_1.name
		assert customers_list[1].name == created_customer.name


# --------------------------------
# ATTACH CARD TO CUSTOMER TESTS
# --------------------------------

@pytest.mark.asyncio
async def test_attach_card_to_customer_not_found():
	customer_repo = CustomerRepository()
	
	# create one customer
	created_customer = await create_customer()

	# create a card
	created_card = await create_card()
		
	# attach non-existing card to customer
	with pytest.raises(NotFoundError):
		customer, card = await customer_repo.attach_card_to_customer(
			created_customer.id, -1) 
		
	# attach non-existing card to customer
	with pytest.raises(NotFoundError):
		customer, card = await customer_repo.attach_card_to_customer(
			created_customer.id, 9999) 
		
	# attach card to non-existing customer
	with pytest.raises(NotFoundError):
		customer, card = await customer_repo.attach_card_to_customer(
			-1, created_card.cardId)

	# attach card to non-existing customer
	with pytest.raises(NotFoundError):
		customer, card = await customer_repo.attach_card_to_customer(
			9999, created_card.cardId)


@pytest.mark.asyncio
async def test_attach_card_to_customer_conflict():
	customer_repo = CustomerRepository()
	
	# create two customers
	created_customer = await create_customer("Paolo Rossi")
	created_customer_1 = await create_customer("Giorgio Neri")

	# create a card
	created_card = await create_card()
		
	# attach card to customer
	customer, card = await customer_repo.attach_card_to_customer(
			created_customer.id, created_card.cardId)
	assert customer.name == created_customer.name
	assert card.cardId == created_card.cardId
	assert card.customer_id == created_customer.id

	# attach same card to another customer
	with pytest.raises(ConflictError):
		customer_1, card = await customer_repo.attach_card_to_customer(
				created_customer_1.id, created_card.cardId)


@pytest.mark.asyncio
async def test_attach_card_to_customer_card_switch():
	customer_repo = CustomerRepository()

	# create one customer
	created_customer = await create_customer()

	# create a card
	created_card = await create_card()
	created_card_1 = await create_card()
		
	# attach card to customer
	customer, card = await customer_repo.attach_card_to_customer(
			created_customer.id, created_card.cardId)
	assert customer.name == created_customer.name
	assert card.cardId == created_card.cardId
	assert card.customer_id == created_customer.id

	# attach same card to same customer
	customer, card = await customer_repo.attach_card_to_customer(
			created_customer.id, created_card.cardId)
	assert customer.name == created_customer.name
	assert card.cardId == created_card.cardId
	assert card.customer_id == created_customer.id

	# attach another card to same customer
	customer, card = await customer_repo.attach_card_to_customer(
			created_customer.id, created_card_1.cardId)
	assert customer.name == created_customer.name
	assert card.cardId == created_card_1.cardId
	assert card.customer_id == created_customer.id

	# attach same card back
	customer, card = await customer_repo.attach_card_to_customer(
			created_customer.id, created_card.cardId)
	assert customer.name == created_customer.name
	assert card.cardId == created_card.cardId
	assert card.customer_id == created_customer.id


# ---------------------------
# UPDATE CUSTOMER TEST
# ---------------------------

@pytest.mark.asyncio
async def test_update_customer_without_card():
	customer_repo = CustomerRepository()

	created_card = await create_card()
	created_customer = await create_customer("Paolo Rossi")
	created_customer_1 = await create_customer("Giorgio Neri")

	await attach_card(created_customer.id, created_card.cardId)

	# update customer without specifying a card
	updated = await customer_repo.update_customer(created_customer.id, "updated", None)
	
	assert updated is not None
	assert updated.name == "updated"

	# ensure card is not deleted
	card = await get_card_by_customer(created_customer.id)
	assert card is not None

	# update customer 1 without specifying a card
	updated = await customer_repo.update_customer(created_customer_1.id, "updated", None)
	
	assert updated is not None
	assert updated.name == "updated"

	# ensure customer 1 still doesn't have a card
	card_1 = await get_card_by_customer(created_customer_1.id)
	assert card_1 is None


@pytest.mark.asyncio
async def test_update_customer_not_found():
	customer_repo = CustomerRepository()
	created_customer = await create_customer()

	# update non existing customer
	with pytest.raises(NotFoundError):
		updated = await customer_repo.update_customer(-1, "updated", None)

	# update non existing customer
	with pytest.raises(NotFoundError):
		updated = await customer_repo.update_customer(9999, "updated", None)

	# update customer with non existing card 
	with pytest.raises(NotFoundError):
		card_dto = CardDTO(card_id=-1, points=0)
		updated = await customer_repo.update_customer(created_customer.id, "updated", card_dto)
		
	# ensure customer name wasn't updated 
	updated = await get_customer_by_id(created_customer.id)
	assert updated.name != "updated"


@pytest.mark.asyncio
async def test_update_customer_with_card():
	customer_repo = CustomerRepository()
	created_customer = await create_customer()

	created_card = await create_card()
	created_card_2 = await create_card()
	await attach_card(created_customer.id, created_card.cardId)

	# update customer specifying a card (same card)
	card_dto = CardDTO(card_id=created_card.cardId, points = 0)
	updated = await customer_repo.update_customer(created_customer.id, "updated", card_dto)
	
	assert updated is not None
	assert updated.name == "updated"

	# ensure card is not deleted
	card = await get_card_by_customer(created_customer.id)
	assert card is not None

	# update customer specifying a card (same card with different points)
	card_dto = CardDTO(card_id=created_card.cardId, points = 1000)
	updated = await customer_repo.update_customer(created_customer.id, "updated 1", card_dto)
	
	assert updated is not None
	assert updated.name == "updated 1"

	# ensure card is not deleted and got its points updated
	card = await get_card_by_customer(created_customer.id)
	assert card is not None
	assert card.points == 1000

	# update customer specifying another card with different
	card_dto = CardDTO(card_id=created_card_2.cardId, points = 1000)
	updated = await customer_repo.update_customer(created_customer.id, "updated 2", card_dto)
	
	assert updated is not None
	assert updated.name == "updated 2"

	# ensure old card is deleted, and new card is attached to customer
	card = await get_card_by_id(created_card.cardId)
	assert card is None

	card_2 = await get_card_by_customer(created_customer.id)
	assert card_2 is not None
	assert card_2.points == 1000


@pytest.mark.asyncio
async def test_update_customer_empty_card():
	customer_repo = CustomerRepository()

	# create a customer
	created_customer = await create_customer()

	# create a card attached to customer
	created_card = await create_card()
	await attach_card(created_customer.id, created_card.cardId)

	# update customer specifying an empty card
	updated = await customer_repo.update_customer(
		created_customer.id, "updated", UpdateCardDTO())
	
	assert updated is not None
	assert updated.name == "updated"

	# ensure old card is deleted, and no new card is attached to customer
	card = await get_card_by_id(created_card.cardId)
	customer_card = await get_card_by_customer(created_customer.id)

	assert card is None
	assert customer_card is None

	
@pytest.mark.asyncio
async def test_update_customer_conflict():
	customer_repo = CustomerRepository()

	# create two customers
	created_customer = await create_customer("Paolo Rossi")
	created_customer_1 = await create_customer("Giorgio Neri")

	# create two card attached to each customer, plus a third card
	created_card = await create_card()
	created_card_1 = await create_card()
	await attach_card(created_customer.id, created_card.cardId)
	await attach_card(created_customer_1.id, created_card_1.cardId)

	# update customer with other customer's card (conflict)
	card_dto =  CardDTO(card_id=created_card_1.cardId, points = 0)
	with pytest.raises(ConflictError):
		updated = await customer_repo.update_customer(
			created_customer.id, "updated", card_dto)

	# ensure customer name wasn't updated 
	updated = await get_customer_by_id(created_customer.id)
	assert updated.name != "updated"

	# ensure same card is attached to customer and not updated 
	card = await get_card_by_customer(created_customer.id)
	assert card is not None
	assert card.cardId == created_card.cardId
	assert card.points != 9999


@pytest.mark.asyncio
async def test_update_customer_invalid_card():
	customer_repo = CustomerRepository()
	created_customer = await create_customer()
	created_card = await create_card()
	await attach_card(created_customer.id, created_card.cardId)

	with pytest.raises(BadRequestError):
		card_dto = CardDTO(card_id=created_card.cardId, points=0)
		card_dto.points = -1
		updated = await customer_repo.update_customer(created_customer.id, "updated", card_dto)
		
	# ensure customer name wasn't updated 
	updated = await get_customer_by_id(created_customer.id)
	assert updated.name != "updated"

	# ensure same card is attached to customer 
	card = await get_card_by_customer(created_customer.id)
	assert card is not None
	assert card.cardId == created_card.cardId

# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_delete_customer_without_card():
	customer_repo = CustomerRepository()
	created_customer = await create_customer()

	# delete customer without a card
	deleted = await customer_repo.delete_customer(created_customer.id)
	assert deleted == True

	# ensure customer is deleted
	customer = await get_customer_by_id(created_customer.id)
	assert customer is None


@pytest.mark.asyncio
async def test_delete_customer_not_found():
	customer_repo = CustomerRepository()

	# delete non-existing customer
	with pytest.raises(NotFoundError):
		deleted = await customer_repo.delete_customer(-1)

	with pytest.raises(NotFoundError):
		deleted = await customer_repo.delete_customer(9999)


@pytest.mark.asyncio
async def test_delete_customer_with_card():
	customer_repo = CustomerRepository()
	created_customer = await create_customer()

	# create a card attached to customer_1
	created_card = await create_card()
	await attach_card(created_customer.id, created_card.cardId)

	# delete customer with a card attached
	deleted = await customer_repo.delete_customer(created_customer.id)
	assert deleted == True

	# ensure customer and card are deleted
	customer = await get_customer_by_id(created_customer.id)
	assert customer is None
	card = await get_card_by_id(created_card.cardId)
	assert card is None