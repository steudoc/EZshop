import asyncio
import pytest
from app.models.DAO.card_dao import CardDAO
from app.models.errors.notfound_error import NotFoundError
from app.repositories.card_repository import CardRepository
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
# CREATE CARD TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_create_card():
	repo = CardRepository()

	card = await repo.create_card()
	card_1 = await repo.create_card()

	# verify auto incremented id
	assert card.cardId == 1
	assert card_1.cardId == 2

	# verify points are 0
	assert card.points == 0
	assert card_1.points == 0


# ---------------------------
# GET CARD TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_get_card_success():
	repo = CardRepository()
	# create a card to get
	created_card = None
	async with await repo._get_session() as session:
		created_card = CardDAO(points=0)
		session.add(created_card)
		await session.commit()

	card = await repo.get_card(created_card.cardId)
	
	# verify card has the same data as the created one
	assert card is not None
	assert card.cardId == created_card.cardId
	assert card.points == created_card.points


@pytest.mark.asyncio
async def test_get_card_not_found():
	repo = CardRepository()

	# searching for a card that doesn't exist
	with pytest.raises(NotFoundError):
		card = await repo.get_card(-1)

	# searching for a card that doesn't exist
	with pytest.raises(NotFoundError):
		card = await repo.get_card(9999)	


# method no longer exists	
# # ---------------------------
# # GET CARD BY ID TESTS
# # ---------------------------

# @pytest.mark.asyncio
# async def test_get_card_by_id():
# 	repo = CardRepository()
# 	# create a card to get
# 	created_card = None
# 	async with await repo._get_session() as session:
# 		created_card = CardDAO(points=0)
# 		session.add(created_card)
# 		await session.commit()

# 	card = await repo.get_card_by_id(created_card.cardId)
	
# 	# verify card has the same data as the created one
# 	assert card is not None
# 	assert card.cardId == created_card.cardId
# 	assert card.points == created_card.points

# 	# searching for a card that doesn't exist
# 	card = await repo.get_card_by_id(-1)
# 	assert card is None

# 	# searching for a card that doesn't exist
# 	card = await repo.get_card_by_id(9999)	
# 	assert card is None
	

# ---------------------------
# UPDATE CARD TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_update_card_success():
	repo = CardRepository()
	# create a card to update
	created_card = None
	async with await repo._get_session() as session:
		created_card = CardDAO(points=0)
		session.add(created_card)
		await session.commit()

	# update the card points a few times
	card = await repo.update_card(created_card.cardId, 100)
	assert card is not None
	assert card.points == 100

	card = await repo.update_card(created_card.cardId, -1000)
	assert card is not None
	assert card.points == -900

	card = await repo.update_card(created_card.cardId, 900)
	assert card is not None
	assert card.points == 0
		

@pytest.mark.asyncio
async def test_update_card_not_found():
	repo = CardRepository()

	# updating a non-existing card should result in NotFoundError
	with pytest.raises(NotFoundError):
		card = await repo.update_card(9999, 100)

# -----------------------------------
# UPDATE CARD WITHOUT SUM TESTS
# -----------------------------------

@pytest.mark.asyncio
async def test_update_card_without_sum_success():
	repo = CardRepository()
	# create a card to update
	created_card = None
	async with await repo._get_session() as session:
		created_card = CardDAO(points=0)
		session.add(created_card)
		await session.commit()

	# update the card points a few times
	card = await repo.update_card_without_sum(created_card.cardId, 100)
	assert card is not None
	assert card.points == 100

	card = await repo.update_card_without_sum(created_card.cardId, -1000)
	assert card is not None
	assert card.points == -1000

	card = await repo.update_card_without_sum(created_card.cardId, 900)
	assert card is not None
	assert card.points == 900


@pytest.mark.asyncio
async def test_update_card_without_sum_not_found():
	repo = CardRepository()

	# updating a non-existing card should result in NotFoundError
	with pytest.raises(NotFoundError):
		card = await repo.update_card_without_sum(9999, 100)

	
# ---------------------------
# DELETE CARD TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_delete_card_success():
	repo = CardRepository()

	created_card = None
	# create a card with a customer attached
	async with await repo._get_session() as session:
		created_card = CardDAO(points=1000)
		session.add(created_card)
		await session.commit()

	# delete card
	deleted = await repo.delete_card(created_card.cardId)
	assert deleted == True


@pytest.mark.asyncio
async def test_delete_card_not_found():
	repo = CardRepository()

	# deleting a non-existing card results in NotFoundError
	with pytest.raises(NotFoundError):
		deleted = await repo.delete_card(-1)

	with pytest.raises(NotFoundError):
		deleted = await repo.delete_card(9999)


# ----------------------------------------------
# CREATE AND ATTACH NEW CARD TO CUSTOMER TESTS
# ----------------------------------------------

# TODO (the method to test probably shouldn't exist)


# ----------------------------------------------
# UPDATE AND ATTACH CARD TO CUSTOMER TESTS
# ----------------------------------------------

@pytest.mark.asyncio
async def test_update_and_attach_to_customer_success():
	repo = CardRepository()
	
	# create a card to update
	created_card = None
	async with await repo._get_session() as session:
		created_card = CardDAO(points=0)
		session.add(created_card)
		await session.commit()

	# update the card points a few times
	card = await repo.update_and_attach_card_to_customer(
		1, created_card.cardId, 100)
	assert card is not None
	assert card.customer_id == 1
	assert card.points == 100

	card = await repo.update_and_attach_card_to_customer(
		2, created_card.cardId, -1000)
	assert card is not None
	assert card.customer_id == 2
	assert card.points == -1000

	card = await repo.update_and_attach_card_to_customer(
		3, created_card.cardId, 0)
	assert card is not None
	assert card.customer_id == 3
	assert card.points == 0


@pytest.mark.asyncio
async def test_update_and_attach_to_customer_not_found():
	repo = CardRepository()

	# updating a non-existing card should result in NotFoundError
	with pytest.raises(NotFoundError):
		card = await repo.update_and_attach_card_to_customer(
		1, 9999, 100)

# ---------------------------
# IS ATTACHED TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_is_attached_success():
	repo = CardRepository()

	card = None
	card_1 = None
	# create a card with a customer attached and one without
	async with await repo._get_session() as session:
		card = CardDAO(points=0)
		card_1 = CardDAO(points=0, customer_id=1)
		session.add(card)
		session.add(card_1)
		await session.commit()
		await session.refresh(card_1)

	# verify card is not attached
	card_attached = await repo.is_attached(card.cardId)
	assert card_attached == False

	# verify card_1 is attached
	card_1_attached = await repo.is_attached(card_1.cardId)
	assert card_1_attached == True


@pytest.mark.asyncio
async def test_is_attached_not_found():
	repo = CardRepository()

	# verifying non-existing card is attached should 
	# result in NotFoundError
	with pytest.raises(NotFoundError):
		attached = await repo.is_attached(-1)

	with pytest.raises(NotFoundError):
		attached = await repo.is_attached(9999)


# ---------------------------
# GET CARD BY CUSTOMER TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_get_card_by_customer_success():
	repo = CardRepository()

	created_card = None
	# create a card with a customer attached
	async with await repo._get_session() as session:
		created_card = CardDAO(points=1000, customer_id=100)
		session.add(created_card)
		await session.commit()
		await session.refresh(created_card)

	# searching card by customer should return created card
	card = await repo.get_card_by_customer(100)
	assert card is not None
	assert card.points == created_card.points
	assert card.customer_id == 100
	assert card.cardId == created_card.cardId


@pytest.mark.asyncio
async def test_get_card_by_customer_not_found():
	repo = CardRepository()

	# searching a card by a non-existing customer
	#  should result in NotFoundError
	with pytest.raises(NotFoundError):
		card = await repo.get_card_by_customer(-1)

	with pytest.raises(NotFoundError):
		card = await repo.get_card_by_customer(9999)
