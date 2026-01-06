import asyncio
import pytest
from sqlalchemy import select
from app.controllers.customer_controller import CustomerController

from app.models.DAO.card_dao import CardDAO
from app.models.DAO.customer_dao import CustomerDAO
from app.models.DTO.customer_dto import CardDTO, CustomerDTO, UpdateCardDTO, UpdateCustomerDTO
from app.models.errors.conflict_error import ConflictError
from app.models.errors.notfound_error import NotFoundError
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
	controller = CustomerController()

	customer_dto = CustomerDTO(id=100, name="Marco Bianchi", card=None)
	customer_dto_1 = CustomerDTO(id=200, name="Paolo Verdi", card=CardDTO(id=1, points=0))
	
	# create a customer without a card
	customer = await controller.create_customer(customer_dto)
	assert customer is not None
	assert customer.id == 1 # give id should be ignored and should start from 1
	assert customer.name == customer_dto.name
	assert customer.card is None

	# create a customer with a card
	customer_1 = await controller.create_customer(customer_dto_1)
	assert customer_1 is not None
	assert customer_1.id == 2 # give id should be ignored and should start from 1
	assert customer_1.name == customer_dto_1.name
	assert customer_1.card is not None
	assert customer_1.card.card_id == 1
	assert customer_1.card.points == 0

	# create a customer with a card that is already assigned
	# (use same card as before, so it should raise an error)
	with pytest.raises(ConflictError):
		customer = await controller.create_customer(customer_dto_1)


# ---------------------------
# GET CUSTOMER TESTS
# ---------------------------


@pytest.mark.asyncio
async def test_get_customer():
	customer_controller = CustomerController()
	
	# create card and customers
	created_card = await create_card()
	created_customer, created_customer_1 = await create_two_customers()

	# attach card to customer 1
	await attach_card(created_customer.id, created_card.cardId)

	# search for the created customer
	customer = await customer_controller.get_customer(created_customer.id)
	assert customer is not None
	assert customer.name == created_customer.name
	assert customer.id == created_customer.id
	assert customer.card is None

	# search for the created customer 1
	customer_1 = await customer_controller.get_customer(created_customer_1.id)
	assert customer_1 is not None
	assert customer_1.name == created_customer_1.name
	assert customer_1.id == created_customer_1.id
	assert customer_1.card is not None
	assert customer_1.card.card_id == 1
	assert customer_1.card.points == 0

	# TODO: ensure expected is None and not error

	# # search for a customer that does not exist
	# with pytest.raises(NotFoundError):
	# 	customer_1 = await customer_controller.get_customer(-1)

	# # search for a customer that does not exist
	# with pytest.raises(NotFoundError):
	# 	customer_1 = await customer_controller.get_customer(9999)

	# search for a customer that does not exist
	customer_1 = await customer_controller.get_customer(-1)
	assert customer_1 is None

	# search for a customer that does not exist
	customer_1 = await customer_controller.get_customer(9999)
	assert customer_1 is None


# ---------------------------
# LIST CUSTOMERS TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_list_customers():
	customer_controller = CustomerController()
	
	# list customers should return empty list
	empty_list = await customer_controller.list_customers()
	assert empty_list is not None
	assert empty_list == []

	# create card and customers
	created_card = await create_card()
	created_customer, created_customer_1 = await create_two_customers()

	# attach card to customer 1
	await attach_card(created_customer.id, created_card.cardId)

	# list customers should contain both customers
	customers_list = await customer_controller.list_customers()
	assert customers_list is not None
	assert len(customers_list) == 2

	# first customer in first position
	if (customers_list[0].name == created_customer.name):
		assert customers_list[1].name == created_customer_1.name
		assert customers_list[1].card is not None
	# first customer in second position
	else:
		assert customers_list[0].name == created_customer_1.name
		assert customers_list[0].card is not None
		assert customers_list[1].name == created_customer.name


# --------------------------------
# ATTACH CARD TO CUSTOMER TESTS
# --------------------------------

@pytest.mark.asyncio
async def test_attach_card_to_customer():
	customer_controller = CustomerController()
	
	# create card and customers
	created_card = await create_card()
	created_customer, created_customer_1 = await create_two_customers()

	# attach non-existing card to customer
	with pytest.raises(NotFoundError):
		customer = await customer_controller.attach_card_to_customer(
			created_customer.id, -1) 
		
	# attach non-existing card to customer
	with pytest.raises(NotFoundError):
		customer = await customer_controller.attach_card_to_customer(
			created_customer.id, 9999) 
		
	# attach card to non-existing customer
	with pytest.raises(NotFoundError):
		customer = await customer_controller.attach_card_to_customer(
			-1, created_card.cardId)

	# attach card to non-existing customer
	with pytest.raises(NotFoundError):
		customer = await customer_controller.attach_card_to_customer(
			9999, created_card.cardId)
		
	# attach card to customer
	customer = await customer_controller.attach_card_to_customer(
			created_customer.id, created_card.cardId)
	assert customer.name == created_customer.name
	assert customer.card is not None
	assert customer.card.card_id == created_card.cardId
	assert customer.card.points == created_card.points

	# attach same card to same customer
	customer = await customer_controller.attach_card_to_customer(
			created_customer.id, created_card.cardId)
	assert customer.name == created_customer.name
	assert customer.card is not None
	assert customer.card.card_id == created_card.cardId
	assert customer.card.points == created_card.points

	# attach same card to another customer
	with pytest.raises(ConflictError):
		customer_1 = await customer_controller.attach_card_to_customer(
				created_customer_1.id, created_card.cardId)
	

# ---------------------------
# UPDATE CUSTOMER TEST
# ---------------------------

@pytest.mark.asyncio
async def test_update_customer():
	customer_controller = CustomerController()
	
	# create cards and customers
	created_card = await create_card()
	created_card_1 = await create_card()
	created_card_2 = await create_card()

	created_customer, created_customer_1 = await create_two_customers()
	
	# attach first two cards to customers
	await attach_card(created_customer.id, created_card.cardId)
	await attach_card(created_customer_1.id, created_card_1.cardId)

	update_dto = UpdateCustomerDTO(name="update 0", card=None)

	# update non existing customer
	updated = await customer_controller.update_customer(-1, update_dto)
	assert updated is None

	# update non existing customer
	updated = await customer_controller.update_customer(9999, update_dto)
	assert updated is None


	# update customer without specifying a card
	update_dto = UpdateCustomerDTO(name="update 1", card=None)
	updated = await customer_controller.update_customer(created_customer.id, update_dto)
	assert updated is not None
	assert updated.name == "update 1"

	# ensure card is not deleted
	card = await get_card_by_customer(created_customer.id)
	assert card is not None


	# update customer specifying a card (same card)
	update_dto = UpdateCustomerDTO(name="update 2", 
					card=UpdateCardDTO(cardId=created_card.cardId, points=0))
	updated = await customer_controller.update_customer(created_customer.id, update_dto)
	assert updated is not None
	assert updated.name == "update 2"

	# ensure card is not deleted
	card = await get_card_by_customer(created_customer.id)
	assert card is not None


	# update customer specifying a card (same card)
	update_dto = UpdateCustomerDTO(name="update 3", 
					card=UpdateCardDTO(cardId=created_card.cardId, points=1000))
	updated = await customer_controller.update_customer(created_customer.id, update_dto)
	assert updated is not None
	assert updated.name == "update 3"

	# ensure card is not deleted
	card = await get_card_by_customer(created_customer.id)
	assert card is not None
	assert card.points == 1000


	# update customer specifying a card (different card with different points)
	update_dto = UpdateCustomerDTO(name="update 4", 
					card=UpdateCardDTO(cardId=created_card_2.cardId, points=1000))
	updated = await customer_controller.update_customer(created_customer.id, update_dto)
	
	assert updated is not None
	assert updated.name == "update 4"

	# ensure old card is deleted
	card = await get_card_by_id(created_card.cardId)
	assert card is None

	# ensure new card is attached to customer 
	card = await get_card_by_customer(created_customer.id)
	assert card is not None
	assert card.cardId == created_card_2.cardId
	assert card.points == 1000

	# update customer specifying an empty card
	update_dto = UpdateCustomerDTO(name="update 5", 
					card={})
	updated = await customer_controller.update_customer(created_customer.id, update_dto)
	
	
	assert updated is not None
	assert updated.name == "update 5"

	# ensure old card is deleted
	card = await get_card_by_id(created_card.cardId)
	assert card is None

	# ensure no new card is attached to customer 
	card = await get_card_by_customer(created_customer.id)
	assert card is None


	# update customer with other customer's card (conflict)
	update_dto = UpdateCustomerDTO(name="update 6", 
					card=UpdateCardDTO(cardId=created_card_1.cardId, points=9999))
	
	with pytest.raises(ConflictError):
		updated = await customer_controller.update_customer(created_customer.id, update_dto)
	
	
	# ensure customer name wasn't updated
	updated = await get_customer_by_id(created_customer.id)
	assert updated.name != "update 6"

	# ensure old card is not deleted or updated
	card = await get_card_by_id(created_card.cardId)
	assert card is not None
	assert card.points != 9999

	# ensure same card is attached to customer 
	card = await get_card_by_customer(created_customer.id)
	assert card is not None
	assert card.cardId == created_card_2.cardId


	# TODO: ensure expected is error and not None
	# update customer 1 with non existing card 
	update_dto = UpdateCustomerDTO(name="update 7", 
					card=UpdateCardDTO(cardId=9999, points=9999))
	with pytest.raises(NotFoundError):
		updated = await customer_controller.update_customer(created_customer_1.id, update_dto)
		
	# ensure customer 1 name wasn't updated 
	updated = await get_customer_by_id(created_customer.id)
	assert updated.name != "update 7"


# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------

# TODO: ensure expected is False and not error

@pytest.mark.asyncio
async def test_attach_card_to_customer():
	customer_controller = CustomerController()
	
	# create card and customers
	created_card = await create_card()
	created_customer, created_customer_1 = await create_two_customers()

	# attach card to customer 1
	await attach_card(created_customer_1.id, created_card.cardId)

	# delete non-existing customer
	deleted = await customer_controller.delete_customer(-1)
	assert deleted == False

	deleted = await customer_controller.delete_customer(9999)
	assert deleted == False

	# delete customer without a card
	deleted = await customer_controller.delete_customer(created_customer.id)
	assert deleted == True

	# ensure customer is deleted
	customer = await get_customer_by_id(created_customer.id)
	assert customer is None

	# delete customer with a card attached
	deleted = await customer_controller.delete_customer(created_customer_1.id)
	assert deleted == True

	# ensure customer 1 and card are deleted
	customer_1 = await get_customer_by_id(created_customer_1.id)
	assert customer_1 is None
	
	card = await get_card_by_id(created_card.cardId)
	assert card is None

