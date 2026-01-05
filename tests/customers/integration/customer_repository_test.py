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
# CREATE CUSTOMER TESTS
# ---------------------------

# ---------------------------
# GET CUSTOMER TESTS
# ---------------------------

# ---------------------------
# LIST CUSTOMERS TESTS
# ---------------------------

# --------------------------------
# ATTACH CARD TO CUSTOMER TESTS
# --------------------------------

# ---------------------------
# UPDATE CUSTOMER TEST
# ---------------------------

# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------
