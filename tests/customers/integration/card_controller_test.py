import asyncio
import pytest
from app.controllers.card_controller import CardController
from app.models.errors.notfound_error import NotFoundError
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
	controller = CardController()

	card = await controller.create_card()
	card_1 = await controller.create_card()

	# verify auto incremented id
	assert card.card_id == 1
	assert card_1.card_id == 2

	# verify points are 0
	assert card.points == 0
	assert card_1.points == 0

# ---------------------------
# GET CARD TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_get_card():
	controller = CardController()
	# create a card to get
	created_card = await controller.create_card()

	card = await controller.get_card(created_card.card_id)
	
	# verify card has the same data as the created one
	assert card is not None
	assert card.card_id == created_card.card_id
	assert card.points == created_card.points

	# searching for a card that doesn't exist
	with pytest.raises(NotFoundError):
		card = await controller.get_card(-1)

	with pytest.raises(NotFoundError):
		card = await controller.get_card(9999)	


# ---------------------------
# MODIFY CARD POINTS TESTS
# ---------------------------

@pytest.mark.asyncio
async def test_modify_card_points():
	controller = CardController()
	# create a card to update
	created_card = await controller.create_card()

	# update the card points a few times
	card = await controller.modify_points_card(created_card.card_id, 100)
	assert card is not None
	assert card.points == 100

	card = await controller.modify_points_card(created_card.card_id, -1000)
	assert card is not None
	assert card.points == -900

	card = await controller.modify_points_card(created_card.card_id, 900)
	assert card is not None
	assert card.points == 0

	# updating a non-existing card should result in None being returned
	with pytest.raises(NotFoundError):
		card = await controller.modify_points_card(9999, 100)
