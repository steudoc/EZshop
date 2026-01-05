import asyncio
import pytest
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

# ---------------------------
# GET CARD TESTS
# ---------------------------

# ---------------------------
# UPDATE CARD TESTS
# ---------------------------

# ---------------------------
# GET CARD BY CUSTOMER TESTS
# ---------------------------

# ---------------------------
# GET CARD BY ID TESTS
# ---------------------------

# ---------------------------
# DELETE CARD TESTS
# ---------------------------

# ----------------------------------------------
# CREATE AND ATTTACH CARD TO CUSTOMER TESTS
# ----------------------------------------------

# ----------------------------------------------
# UPDATE AND ATTTACH CARD TO CUSTOMER TESTS
# ----------------------------------------------

# ---------------------------
# IS ATTACHED TESTS
# ---------------------------

# -----------------------------------
# UPDATE CARD WITHOUT SUM TESTS
# -----------------------------------

