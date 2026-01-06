import asyncio
import pytest
from app.models.DAO.card_dao import CardDAO
from app.models.DAO.customer_dao import CustomerDAO
from app.models.errors.conflict_error import ConflictError
from app.models.errors.notfound_error import NotFoundError
from app.repositories.card_repository import CardRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.mapper_service import carddao_to_response_dto, customerdao_to_responsedto
from main import app
from init_db import reset, init_db

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
	

# ---------------------------
# CREATE CUSTOMER TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_create_customer():
	customer_repo = CustomerRepository()
	card_repo = CardRepository()

	customer_name = "Marco Bianchi"
	created_card = await card_repo.create_card()
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
	
	customer_name = "Marco Bianchi"
	created_customer = None
	# create a customer 
	async with await customer_repo._get_session() as session:
		created_customer = CustomerDAO(name = customer_name)
		session.add(created_customer)
		await session.commit()

	# search for the created customer
	customer = await customer_repo.get_customer(created_customer.id)
	assert customer is not None
	assert customer.name == customer_name
	assert customer.id == created_customer.id

	# search for a customer that does not exist
	with pytest.raises(NotFoundError):
		customer_1 = await customer_repo.get_customer(-1)

	# search for a customer that does not exist
	with pytest.raises(NotFoundError):
		customer_1 = await customer_repo.get_customer(9999)


# ---------------------------
# LIST CUSTOMERS TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_list_customers():
	customer_repo = CustomerRepository()
	
	customer_name = "Marco Bianchi"
	customer_name_1 = "Paolo Rossi"
	created_customer = None
	created_customer_1 = None

	# list customers should return empty list
	empty_list = await customer_repo.list_customers()
	assert empty_list is not None
	assert empty_list == []

	# create customers
	async with await customer_repo._get_session() as session:
		created_customer = CustomerDAO(name = customer_name)
		created_customer_1 = CustomerDAO(name = customer_name_1)
		session.add(created_customer)
		session.add(created_customer_1)

		await session.commit()

	# list customers should contain both customers
	customers_list = await customer_repo.list_customers()
	assert customers_list is not None
	assert len(customers_list) == 2

	# first customer in first position
	if (customers_list[0].name == customer_name):
		assert customers_list[1].name == customer_name_1
	# first customer in second position
	else:
		assert customers_list[0].name == customer_name_1
		assert customers_list[1].name == customer_name


# --------------------------------
# ATTACH CARD TO CUSTOMER TESTS
# --------------------------------

@pytest.mark.asyncio
async def test_attach_card_to_customer():
	customer_repo = CustomerRepository()
	card_repo = CardRepository()
	
	customer_name = "Marco Bianchi"
	customer_name_1 = "Paolo Rossi"
	created_customer = None
	created_customer_1 = None

	# create two customers
	async with await customer_repo._get_session() as session:
		created_customer = CustomerDAO(name = customer_name)
		created_customer_1 = CustomerDAO(name = customer_name_1)
		session.add(created_customer)
		session.add(created_customer_1)

		await session.commit()

	# create a card
	created_card = None
	async with await card_repo._get_session() as session:
		created_card = CardDAO(points=0)
		session.add(created_card)
		await session.commit()
		
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



# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_attach_card_to_customer():
	customer_repo = CustomerRepository()
	card_repo = CardRepository()
	
	customer_name = "Marco Bianchi"
	customer_name_1 = "Paolo Rossi"
	created_customer = None
	created_customer_1 = None

	# create two customers, onw with a card attached
	async with await customer_repo._get_session() as session:
		created_customer = CustomerDAO(name = customer_name)
		created_customer_1 = CustomerDAO(name = customer_name_1)
		session.add(created_customer)
		session.add(created_customer_1)

		await session.commit()

	# create a card attached to customer_1
	created_card = None
	async with await card_repo._get_session() as session:
		created_card = CardDAO(points=0, customer_id=created_customer_1.id)
		session.add(created_card)
		await session.commit()
		

	# delete non-existing customer
	deleted = await customer_repo.delete_customer(-1)
	assert deleted == False

	deleted = await customer_repo.delete_customer(9999)
	assert deleted == False

	# delete customer without a card
	deleted = await customer_repo.delete_customer(created_customer.id)
	assert deleted == True

	# ensure customer is deleted
	async with await customer_repo._get_session() as session:
		customer = await session.get(CustomerDAO, created_customer.id)
		assert customer is None

	# delete customer with a card attached
	deleted = await customer_repo.delete_customer(created_customer_1.id)
	assert deleted == True

	# ensure customer and card are deleted
	async with await customer_repo._get_session() as session:
		customer = await session.get(CustomerDAO, created_customer_1.id)
		assert customer is None
		card = await session.get(CardDAO, created_card.cardId)
		assert card is None
