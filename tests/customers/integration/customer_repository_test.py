import asyncio
import pytest
from sqlalchemy import select
from app.models.DAO.card_dao import CardDAO
from app.models.DAO.customer_dao import CustomerDAO
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
async def test_get_customer():
	customer_repo = CustomerRepository()
	
	# create a customer
	created_customer, dummy = await create_two_customers()

	# search for the created customer
	customer = await customer_repo.get_customer(created_customer.id)
	assert customer is not None
	assert customer.name == created_customer.name
	assert customer.id == created_customer.id

	# # search for a customer that does not exist
	# with pytest.raises(NotFoundError):
	# 	customer_1 = await customer_repo.get_customer(-1)

	# # search for a customer that does not exist
	# with pytest.raises(NotFoundError):
	# 	customer_1 = await customer_repo.get_customer(9999)

	# TODO: ensure expected is None and not error

	# search for a customer that does not exist
	customer_1 = await customer_repo.get_customer(-1)
	assert customer_1 is None

	# search for a customer that does not exist
	customer_1 = await customer_repo.get_customer(9999)
	assert customer_1 is None

# ---------------------------
# LIST CUSTOMERS TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_list_customers():
	customer_repo = CustomerRepository()

	# list customers should return empty list
	empty_list = await customer_repo.list_customers()
	assert empty_list is not None
	assert empty_list == []

	# create two customers
	created_customer, created_customer_1 = await create_two_customers()

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
async def test_attach_card_to_customer():
	customer_repo = CustomerRepository()
	
	# create two customers
	created_customer, created_customer_1 = await create_two_customers()

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

	# attach same card to another customer
	with pytest.raises(ConflictError):
		customer_1, card = await customer_repo.attach_card_to_customer(
				created_customer_1.id, created_card.cardId)
	

# ---------------------------
# UPDATE CUSTOMER TEST
# ---------------------------

@pytest.mark.asyncio
async def test_update_customer():
	customer_repo = CustomerRepository()

	# create two customers
	created_customer, created_customer_1 = await create_two_customers()

	# create two card attached to each customer, plus a third card
	created_card = await create_card()
	created_card_1 = await create_card()
	created_card_2 = await create_card()
	await attach_card(created_customer.id, created_card.cardId)
	await attach_card(created_customer_1.id, created_card_1.cardId)

	# update non existing customer
	updated = await customer_repo.update_customer(
		-1, "update 0", None)
	
	assert updated is None

	# update non existing customer
	updated = await customer_repo.update_customer(
		9999, "update 0", None)
	
	assert updated is None


	# update customer without specifying a card
	updated = await customer_repo.update_customer(
		created_customer.id, "update 1", None)
	
	assert updated is not None
	assert updated.name == "update 1"

	# ensure card is not deleted
	card = await get_card_by_customer(created_customer.id)
	assert card is not None


	# update customer specifying a card (same card)
	card_dto = carddao_to_response_dto(created_card)
	updated = await customer_repo.update_customer(
		created_customer.id, "update 2", card_dto)
	
	assert updated is not None
	assert updated.name == "update 2"

	# ensure card is not deleted
	card = await get_card_by_customer(created_customer.id)
	assert card is not None


	# update customer specifying a card (same card with different points)
	card_dto = carddao_to_response_dto(created_card)
	card_dto.points = 1000
	updated = await customer_repo.update_customer(
		created_customer.id, "update 3", card_dto)
	
	assert updated is not None
	assert updated.name == "update 3"

	# ensure card is not deleted and got its points updated
	card = await get_card_by_customer(created_customer.id)
	assert card is not None
	assert card.points == 1000


	# update customer specifying a card (different card with different points)
	card_dto = carddao_to_response_dto(created_card_2)
	card_dto.points = 1000
	updated = await customer_repo.update_customer(
		created_customer.id, "update 4", card_dto)
	
	assert updated is not None
	assert updated.name == "update 4"

	# ensure old card is deleted, and new card is attached to customer
	card = await get_card_by_id(created_card.cardId)
	assert card is None

	card_2 = await get_card_by_customer(created_customer.id)
	assert card_2 is not None
	assert card_2.points == 1000


	# update customer specifying an empty card
	updated = await customer_repo.update_customer(
		created_customer.id, "update 5", {})
	
	assert updated is not None
	assert updated.name == "update 5"

	# ensure old card is deleted, and no new card is attached to customer
	card_2 = await get_card_by_id(created_card_2.cardId)
	customer_card = await get_card_by_customer(created_customer)

	assert card_2 is None
	assert customer_card is None

	
	# update customer with other customer's card (conflict)
	with pytest.raises(ConflictError):
		updated = await customer_repo.update_customer(
			created_customer.id, "update 6", created_card_1.cardId)

	# ensure customer name wasn't updated 
	updated = await get_customer_by_id(created_customer.id)
	assert updated.name != "update 6"


	# TODO: ensure expected is error and not None
	# update customer 1 with non existing card 
	with pytest.raises(NotFoundError):
		updated = await customer_repo.update_customer(
			created_customer_1.id, "update 7", 9999)
		
	# ensure customer 1 name wasn't updated 
	updated = await get_customer_by_id(created_customer_1.id)
	assert updated.name != "update 7"


# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------



@pytest.mark.asyncio
async def test_attach_card_to_customer():
	customer_repo = CustomerRepository()

	created_customer, created_customer_1 = await create_two_customers()

	# create a card attached to customer_1
	created_card = await create_card()
	await attach_card(created_customer_1.id, created_card.cardId)
		
	# TODO: ensure expected is False and not error
	# delete non-existing customer
	deleted = await customer_repo.delete_customer(-1)
	assert deleted == False

	deleted = await customer_repo.delete_customer(9999)
	assert deleted == False

	# delete customer without a card
	deleted = await customer_repo.delete_customer(created_customer.id)
	assert deleted == True

	# ensure customer is deleted
	customer = await get_customer_by_id(created_customer.id)
	assert customer is None

	# delete customer with a card attached
	deleted = await customer_repo.delete_customer(created_customer_1.id)
	assert deleted == True

	# ensure customer and card are deleted
	customer = await get_customer_by_id(created_customer_1.id)
	assert customer is None
	card = await get_card_by_id(created_card.cardId)
	assert card is None
